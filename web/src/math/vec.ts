// SPDX-License-Identifier: Apache-2.0

import { MAP_R_OPTICAL } from "./constants.ts";

export type Vec3 = [number, number, number];

function rowDot(row: readonly number[], v: Vec3): number {
  return row[0]! * v[0] + row[1]! * v[1] + row[2]! * v[2];
}

export function matVec3(m: readonly (readonly number[])[], v: Vec3): Vec3 {
  return [rowDot(m[0]!, v), rowDot(m[1]!, v), rowDot(m[2]!, v)];
}

export function matTVec3(m: readonly (readonly number[])[], v: Vec3): Vec3 {
  return [
    m[0]![0]! * v[0] + m[1]![0]! * v[1] + m[2]![0]! * v[2],
    m[0]![1]! * v[0] + m[1]![1]! * v[1] + m[2]![1]! * v[2],
    m[0]![2]! * v[0] + m[1]![2]! * v[1] + m[2]![2]! * v[2],
  ];
}

export function add3(a: Vec3, b: Vec3): Vec3 {
  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
}

export function sub3(a: Vec3, b: Vec3): Vec3 {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

export function scale3(v: Vec3, s: number): Vec3 {
  return [v[0] * s, v[1] * s, v[2] * s];
}

export function norm3(v: Vec3): number {
  return Math.hypot(v[0], v[1], v[2]);
}

export function mapFromOptical(pOpt: Vec3, t: Vec3): Vec3 {
  return add3(matVec3(MAP_R_OPTICAL, pOpt), t);
}
