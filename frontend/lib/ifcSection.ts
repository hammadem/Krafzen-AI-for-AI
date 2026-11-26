export type Vec3 = [number, number, number];

/** Clip a triangle to an axis-aligned half space, preserving source geometry.
 * Output is a triangle fan, not a fabricated cap or a measured section area. */
export function clipIfcTriangle(points: [Vec3, Vec3, Vec3], axis: number, plane: number): Vec3[][] {
    if (![0,1,2].includes(axis) || !Number.isFinite(plane) ||
        points.some(p=>p.some(v=>!Number.isFinite(v)))) return [];
    const polygon: Vec3[] = [];
    for (let i=0;i<3;i++) {
        const a=points[i], b=points[(i+1)%3];
        const insideA=a[axis]<=plane, insideB=b[axis]<=plane;
        if (insideA) polygon.push(a);
        if (insideA!==insideB) {
            const t=(plane-a[axis])/(b[axis]-a[axis]);
            const p: Vec3=[a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),a[2]+t*(b[2]-a[2])];
            p[axis]=plane; polygon.push(p);
        }
    }
    const out: Vec3[][]=[];
    for(let i=1;i+1<polygon.length;i++) {
        const a=polygon[0],b=polygon[i],c=polygon[i+1];
        if(a.every((v,k)=>v===b[k])||a.every((v,k)=>v===c[k])||b.every((v,k)=>v===c[k])) continue;
        out.push([a,b,c]);
    }
    return out;
}
