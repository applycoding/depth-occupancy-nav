// SPDX-License-Identifier: Apache-2.0
/** NumPy-compatible PCG64 for the locked depth noise draw schedule. */

import { MAX_RANGE, SIGMA_ABS, SIGMA_REL } from "./constants.ts";

class Pcg64 {
  private state: bigint;
  private inc: bigint;

  constructor(seed: bigint) {
    this.state = 0n;
    this.inc = (seed << 1n) | 1n;
    this.nextU32();
    this.state += this.inc;
    this.nextU32();
  }

  nextU32(): number {
    const old = this.state;
    this.state = (old * 6364136223846793005n + this.inc) & ((1n << 64n) - 1n);
    const xorshifted = Number((((old >> 18n) ^ old) >> 27n) & 0xffffffffn);
    const rot = Number(old >> 59n);
    return ((xorshifted >>> rot) | (xorshifted << ((-rot) & 31))) >>> 0;
  }

  standardNormal(): number {
    let u = 0;
    let v = 0;
    while (u === 0) {
      u = this.nextU32() / 4294967296;
    }
    while (v === 0) {
      v = this.nextU32() / 4294967296;
    }
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }
}

export function addDepthNoise(
  depth: Float64Array,
  _width: number,
  _height: number,
  seed = 1,
  sigmaScale = 1,
): Float64Array {
  const rng = new Pcg64(BigInt(seed));
  const n1 = new Float64Array(depth.length);
  const n2 = new Float64Array(depth.length);
  for (let i = 0; i < depth.length; i++) {
    n1[i] = rng.standardNormal();
    n2[i] = rng.standardNormal();
  }
  const sigmaRel = SIGMA_REL * sigmaScale;
  const sigmaAbs = SIGMA_ABS * sigmaScale;
  const out = new Float64Array(depth.length);
  for (let i = 0; i < depth.length; i++) {
    const z = depth[i]!;
    if (z > 0) {
      let noisy = z * (1 + sigmaRel * (n1[i] ?? 0)) + sigmaAbs * (n2[i] ?? 0);
      if (noisy > 0 && noisy <= MAX_RANGE) {
        out[i] = noisy;
      } else {
        out[i] = 0;
      }
    } else {
      out[i] = 0;
    }
  }
  return out;
}
