import {clipIfcTriangle, type Vec3} from "@/lib/ifcSection";
import {describe,it,expect} from "vitest";
const triangle: [Vec3,Vec3,Vec3]=[[0,0,0],[2,0,0],[0,2,0]];
describe("IFC section clipping",()=>{
 it("retains full triangles inside and removes those outside",()=>{
   expect(clipIfcTriangle(triangle,0,3)).toEqual([triangle]);
   expect(clipIfcTriangle(triangle,0,-1)).toEqual([]);
 });
 it("clips crossed edges at the actual world coordinate",()=>{
   const result=clipIfcTriangle(triangle,0,1);
   expect(result).toHaveLength(2);
   expect(result.flat().every(p=>p[0]<=1)).toBe(true);
   expect(result.flat()).toContainEqual([1,1,0]);
   expect(result.flat()).toContainEqual([1,0,0]);
 });
});
