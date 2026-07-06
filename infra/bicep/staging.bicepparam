using './main.bicep'

// Non-secret parameters for the staging environment. The PG admin password is
// NEVER committed — supply it at deploy time from Key Vault or the CI secret:
//   az deployment group create -g rg-fiq-staging -f main.bicep \
//     --parameters staging.bicepparam --parameters pgAdminPassword=$PG_PASSWORD
param env = 'staging'
param namePrefix = 'fiq'
param location = 'germanywestcentral'
param pgAdminLogin = 'fiqadmin'
