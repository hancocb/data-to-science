import { AxiosResponse } from 'axios';
import { useMemo, useState } from 'react';
import { useLoaderData } from 'react-router-dom';

import DashboardUserList from './DashboardUserList';
import SearchBar from './SearchBar';
import StatCard from './StatCard';
import { User } from '../../../AuthContext';

import api from '../../../api';
import { sorter } from '../../utils';

export async function loader() {
  const response: AxiosResponse<User[]> = await api.get('/users');
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

/**
 * Return number of users that joined in last N days.
 * @param users List of users on platform.
 * @param nDays Number of days.
 * @returns Users registered within number of days.
 */
function joinedInLastNDays(users: User[], nDays: number): number {
  const pastDate = new Date();
  // update today to today's date - number of days
  pastDate.setDate(pastDate.getDate() - nDays);
  const filteredUsers = users.filter(
    ({ created_at }) => new Date(created_at).getTime() > pastDate.getTime()
  );
  return filteredUsers.length;
}

export default function DashboardUsers() {
  const [searchTerm, setSearchTerm] = useState<string>('');

  const users = useLoaderData() as User[];

  const updateSearchTerm = (newSearchTerm: string): void =>
    setSearchTerm(newSearchTerm);

  const filteredUsers = useMemo(() => {
    // If searchTerm is empty, return all users
    if (searchTerm === '') {
      return users
        .slice()
        .sort((a, b) =>
          sorter(a.last_name.toLowerCase(), b.last_name.toLowerCase())
        );
    }

    const lowerSearchTerm = searchTerm.toLowerCase();

    return users
      .filter(
        (user) =>
          user.first_name.toLowerCase().includes(lowerSearchTerm) ||
          user.last_name.toLowerCase().includes(lowerSearchTerm) ||
          user.email.toLowerCase().includes(searchTerm)
      )
      .sort((a, b) =>
        sorter(a.last_name.toLowerCase(), b.last_name.toLowerCase())
      );
  }, [searchTerm, users]);

  return (
    <section className="w-full bg-white">
      <div className="flex flex-col gap-8 mx-auto max-w-screen-xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            Users
          </h2>

          <p className="mt-4 text-gray-500 sm:text-xl">
            List of registered users on this D2S instance.
          </p>
        </div>

        <div>
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard title="Total users" value={users.length} />
            <StatCard title="Last 7 days" value={joinedInLastNDays(users, 7)} />
            <StatCard
              title="Last 30 days"
              value={joinedInLastNDays(users, 30)}
            />
          </dl>
        </div>

        <SearchBar
          searchTerm={searchTerm}
          updateSearchTerm={updateSearchTerm}
        />

        <DashboardUserList users={filteredUsers} />
      </div>
    </section>
  );
}
