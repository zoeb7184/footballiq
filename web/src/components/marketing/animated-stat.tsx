"use client";

import { useEffect, useRef, useState } from "react";
import { animate, useInView, useReducedMotion } from "framer-motion";
import { fmtNum } from "@/lib/format";

/** Counts up from 0 once it scrolls into view. Reduced motion: jumps straight to value. */
export function AnimatedStat({ value }: { value: number | null | undefined }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "0px 0px -80px 0px" });
  const [display, setDisplay] = useState(0);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (!inView || value == null || reduceMotion) return;
    const controls = animate(0, value, {
      duration: 1.2,
      ease: "easeOut",
      onUpdate: (v) => setDisplay(Math.round(v)),
    });
    return () => controls.stop();
  }, [inView, value, reduceMotion]);

  return (
    <span ref={ref} className="num text-2xl font-bold text-accent sm:text-3xl">
      {value == null ? "—" : fmtNum(reduceMotion ? value : display)}
    </span>
  );
}
