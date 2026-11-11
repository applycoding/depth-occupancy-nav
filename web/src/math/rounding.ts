// SPDX-License-Identifier: Apache-2.0
/** Python banker's rounding (half to even). */

export function roundHalfEven(x: number): number {
  const f = Math.floor(x);
  const frac = x - f;
  if (Math.abs(frac - 0.5) > 1e-12 && Math.abs(frac + 0.5) > 1e-12) {
    return Math.round(x);
  }
  return f % 2 === 0 ? f : f + 1;
}
