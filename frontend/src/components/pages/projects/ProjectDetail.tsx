import axios, { AxiosResponse } from 'axios';
import { useEffect, useState } from 'react';
import { Params, useLoaderData, useLocation, useParams } from 'react-router-dom';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';

import { User } from '../../../AuthContext';
import { useProjectContext } from './ProjectContext';

import { Flight, Project, ProjectLoaderData } from './Project';
import { ProjectMember } from './ProjectAccess';
import ProjectCampaigns from './ProjectCampaigns';
import ProjectDetailEditForm from './ProjectDetailEditForm';
import { Team } from '../teams/Teams';
import ProjectFlights from './ProjectFlights';
import { getProjectMembers } from './ProjectContext/ProjectContext';
import ProjectVectorData from './ProjectVectorData';

export async function loader({ params }: { params: Params<string> }) {
  const profile = localStorage.getItem('userProfile');
  const user: User | null = profile ? JSON.parse(profile) : null;
  if (!user) return null;

  try {
    const project: AxiosResponse<Project> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}`
    );
    const project_member: AxiosResponse<ProjectMember> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/members/${
        user.id
      }`
    );
    const flights: AxiosResponse<Flight[]> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/projects/${params.projectId}/flights`
    );
    const teams: AxiosResponse<Team[]> = await axios.get(
      `${import.meta.env.VITE_API_V1_STR}/teams`
    );

    if (project && project_member && flights && teams) {
      const teamsf = teams.data;
      teamsf.unshift({ title: 'No team', id: '', is_owner: false, description: '' });
      return {
        project: project.data,
        role: project_member.data.role,
        flights: flights.data,
        teams: teamsf,
      };
    } else {
      return {
        project: null,
        role: null,
        flights: [],
        teams: [],
      };
    }
  } catch (err) {
    return {
      project: null,
      role: null,
      flights: [],
      teams: [],
    };
  }
}

export default function ProjectDetail() {
  const [selectedIndex, setSelectedIndex] = useState(0);

  const { project, role, flights, teams } = useLoaderData() as ProjectLoaderData;
  const location = useLocation();
  const params = useParams();

  const {
    projectRole,
    flights: flightsPrev,
    flightsDispatch,
    flightsFilterSelection,
    flightsFilterSelectionDispatch,
    projectDispatch,
    projectMembersDispatch,
    projectRoleDispatch,
  } = useProjectContext();

  useEffect(() => {
    if (location.state && location.state.selectedIndex) {
      setSelectedIndex(location.state.selectedIndex);
    }
  }, [location.state]);

  useEffect(() => {
    if (role) projectRoleDispatch({ type: 'set', payload: role });
  }, [role]);

  useEffect(() => {
    // @ts-ignore
    if (project) projectDispatch({ type: 'set', payload: project });
  }, [project]);

  useEffect(() => {
    // update project members if team changes
    if (project) getProjectMembers(params, projectMembersDispatch);
  }, [project.team_id]);

  useEffect(() => {
    if (flights) flightsDispatch({ type: 'set', payload: flights });
    // check filter option for new flight if it is the first flight with its sensor
    if (flights && flightsPrev) {
      // no previous flights, so select any sensor in flights
      if (flightsPrev.length === 0) {
        flightsFilterSelectionDispatch({
          type: 'set',
          payload: [...new Set(flights.map(({ sensor }) => sensor))],
        });
      } else {
        // compare previous sensors with sensor in new flights
        const prevSensors = flightsPrev.map(({ sensor }) => sensor);
        const newSensors = flights
          .filter(
            ({ sensor }) =>
              prevSensors.indexOf(sensor) < 0 &&
              flightsFilterSelection.indexOf(sensor) < 0
          )
          .map(({ sensor }) => sensor);
        // if any new sensors were found, add to filter selection options and check
        if (newSensors.length > 0) {
          flightsFilterSelectionDispatch({
            type: 'set',
            payload: [...flightsFilterSelection, ...newSensors],
          });
        }
      }
    }
  }, [flights]);

  if (project) {
    return (
      <div className="flex flex-col h-full gap-4 p-4">
        {projectRole === 'owner' || projectRole === 'manager' ? (
          <ProjectDetailEditForm project={project} teams={teams} />
        ) : (
          <div>
            <span className="text-lg font-bold mb-0">{project.title}</span>
            <span className="text-gray-600">{project.description}</span>
          </div>
        )}
        <div className="grow min-h-0">
          <TabGroup selectedIndex={selectedIndex} onChange={setSelectedIndex}>
            <TabList>
              <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-28 shrink-0 rounded-lg p-2 font-medium">
                Flights
              </Tab>
              <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-28 shrink-0 rounded-lg p-2 font-medium">
                Map Layers
              </Tab>
              <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-28 shrink-0 rounded-lg p-2 font-medium">
                Field Data
              </Tab>
            </TabList>
            <hr className="my-4 border-gray-700" />
            <TabPanels>
              <TabPanel>
                <ProjectFlights />
              </TabPanel>
              <TabPanel>
                <ProjectVectorData />
              </TabPanel>
              <TabPanel>
                <ProjectCampaigns />
              </TabPanel>
            </TabPanels>
          </TabGroup>
        </div>
      </div>
    );
  } else {
    return (
      <div className="flex flex-col h-full gap-4 p-4">
        Unable to load selected project
      </div>
    );
  }
}
