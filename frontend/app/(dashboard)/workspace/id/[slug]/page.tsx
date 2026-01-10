import ProjectUI from "./ProjectUI";

export default async function UserProjects({ params }: {
    params: Promise<{ slug: string }>
}) {
    const { slug } = await params;

    return (
        <>
            <ProjectUI slug={slug} />
        </>
    );
}


