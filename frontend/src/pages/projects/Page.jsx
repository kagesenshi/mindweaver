import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useProjects } from '../../hooks/useResources';
import ListingView from './ListingView';
import ServiceView from './ServiceView';

const ProjectsPage = () => {
    const context = useOutletContext();
    const projectsHook = useProjects();
    const [selectedProjectId, setSelectedProjectId] = useState(null);

    const handleSelectProject = (id) => {
        setSelectedProjectId(id);
    };

    const selectedProject = projectsHook.projects.find(p => p.id === selectedProjectId);

    if (selectedProject) {
        return (
            <ServiceView
                context={context}
                selectedProjectId={selectedProjectId}
                selectedProject={selectedProject}
                onBack={() => setSelectedProjectId(null)}
                projectsHook={projectsHook}
            />
        );
    }

    return (
        <ListingView
            context={context}
            projectsHook={projectsHook}
            onSelectProject={handleSelectProject}
        />
    );
};

export default ProjectsPage;
