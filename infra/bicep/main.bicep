// FootballIQ — Azure infrastructure (portfolio tier) per docs/infra/azure-architecture.md.
// Pure placement of the committed design: ACA for API + jobs, PostgreSQL
// Flexible Server (pgvector native) for all schemas, ACR/KV/Blob/Log Analytics.
// Validate:  az bicep build --file infra/bicep/main.bicep
// Deploy:    az deployment group create -g <rg> -f infra/bicep/main.bicep -p env=staging pgAdminPassword=<secret>

targetScope = 'resourceGroup'

@description('Short name prefix for resources.')
param namePrefix string = 'fiq'

@description('Deployment environment.')
@allowed(['staging', 'prod'])
param env string = 'staging'

@description('Azure region. Germany West Central for the data-residency narrative.')
param location string = 'germanywestcentral'

@description('PostgreSQL administrator login.')
param pgAdminLogin string = 'fiqadmin'

@description('PostgreSQL administrator password.')
@secure()
param pgAdminPassword string

@description('Container image for the API (ACR path : tag).')
param apiImage string = 'mcr.microsoft.com/azuredocs/aci-helloworld:latest'

var suffix = uniqueString(resourceGroup().id, env)
var tags = {
  project: 'footballiq'
  environment: env
  managedBy: 'bicep'
}
// Prod gets a slightly larger PG SKU; staging stays cheapest (cost §10).
var pgSku = env == 'prod' ? 'Standard_B2s' : 'Standard_B1ms'

// ---- observability ---------------------------------------------------------
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${namePrefix}-log-${env}'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// ---- container registry (shared-tier in reality; here for a self-contained demo) ----
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: '${namePrefix}acr${suffix}'
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: false }
}

// ---- key vault (true secrets: LLM key, PG admin) ---------------------------
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${namePrefix}kv${suffix}'
  location: location
  tags: tags
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
  }
}

// ---- blob storage (raw landing zone, model artifacts, .pbix) ---------------
resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${namePrefix}st${suffix}'
  location: location
  tags: tags
  sku: { name: env == 'prod' ? 'Standard_GRS' : 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
  }
  resource blob 'blobServices@2023-01-01' = {
    name: 'default'
    resource raw 'containers@2023-01-01' = { name: 'raw' }
    resource artifacts 'containers@2023-01-01' = { name: 'artifacts' }
  }
}

// ---- postgresql flexible server (all schemas; pgvector native) -------------
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: '${namePrefix}-pg-${env}-${suffix}'
  location: location
  tags: tags
  sku: { name: pgSku, tier: 'Burstable' }
  properties: {
    version: '16'
    administratorLogin: pgAdminLogin
    administratorLoginPassword: pgAdminPassword
    storage: { storageSizeGB: 32 }
    backup: {
      backupRetentionDays: env == 'prod' ? 35 : 7
      geoRedundantBackup: env == 'prod' ? 'Enabled' : 'Disabled'
    }
    highAvailability: { mode: 'Disabled' }
  }

  resource database 'databases@2023-06-01-preview' = {
    name: 'footballiq'
  }

  // Allowlist pgvector so `CREATE EXTENSION vector` works (RAG deploys unchanged).
  resource extensions 'configurations@2023-06-01-preview' = {
    name: 'azure.extensions'
    properties: { value: 'VECTOR', source: 'user-override' }
  }

  // Portfolio tier (§5): public endpoint + firewall allowlist, no VNet.
  resource allowAzure 'firewallRules@2023-06-01-preview' = {
    name: 'AllowAzureServices'
    properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
  }
}

// ---- container apps environment --------------------------------------------
resource acaEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${namePrefix}-aca-${env}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// ---- API container app (managed identity; ACR pull; external ingress) -------
var dbUrl = 'postgresql+psycopg://${pgAdminLogin}:${pgAdminPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/footballiq'

resource api 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-api-${env}'
  location: location
  tags: tags
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: acaEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        { server: registry.properties.loginServer, identity: 'system' }
      ]
      secrets: [
        { name: 'db-url', value: dbUrl }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'FIQ_DATABASE_URL', secretRef: 'db-url' }
          ]
        }
      ]
      scale: {
        minReplicas: env == 'prod' ? 1 : 0
        maxReplicas: 3
      }
    }
  }
}

// AcrPull for the API's managed identity so it can pull the private image.
resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, api.id, 'AcrPull')
  scope: registry
  properties: {
    principalId: api.identity.principalId
    principalType: 'ServicePrincipal'
    // AcrPull built-in role.
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
  }
}

output apiFqdn string = api.properties.configuration.ingress.fqdn
output registryLoginServer string = registry.properties.loginServer
output postgresFqdn string = postgres.properties.fullyQualifiedDomainName
output keyVaultName string = keyVault.name
