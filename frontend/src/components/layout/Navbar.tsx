import { Fragment, useContext } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Disclosure, Menu, Transition } from '@headlessui/react';
import { Bars3Icon, ChevronDownIcon, XMarkIcon } from '@heroicons/react/24/outline';

import AuthContext from '../../AuthContext';
import { generateRandomProfileColor } from '../pages/auth/Profile';

import brandLogo from '../../assets/d2s-logo-white-horizontal.png';

const navigation = [
  { name: 'HOMEPAGE', href: '/home' },
  { name: 'WORKSPACE', href: '/projects' },
  { name: 'MY TEAMS', href: '/teams' },
];

function classNames(...classes: [string, string]) {
  return classes.filter(Boolean).join(' ');
}

export default function Navbar() {
  const location = useLocation();
  const { user } = useContext(AuthContext);
  return (
    <Disclosure as="nav" className="bg-primary">
      {({ open }) => (
        <>
          <div className="mx-auto px-2 sm:px-6 lg:px-8">
            <div className="relative flex h-16 items-center justify-between">
              {user ? (
                <div className="absolute inset-y-0 left-0 flex items-center sm:hidden">
                  {/* Mobile menu button*/}
                  <Disclosure.Button className="relative inline-flex items-center justify-center rounded-md p-2 text-white focus:bg-[#365173]">
                    <span className="absolute -inset-0.5" />
                    <span className="sr-only">Open main menu</span>
                    {open ? (
                      <XMarkIcon className="block h-6 w-6" aria-hidden="true" />
                    ) : (
                      <Bars3Icon className="block h-6 w-6" aria-hidden="true" />
                    )}
                  </Disclosure.Button>
                </div>
              ) : null}
              <div className="flex flex-1 items-center justify-center sm:items-stretch sm:justify-start">
                <div className="flex flex-shrink-0 items-center">
                  <Link to="/">
                    <img className="h-8 w-auto" src={brandLogo} alt="Brand logo" />
                  </Link>
                </div>
                {user ? (
                  <div className="hidden sm:ml-6 sm:block">
                    <div className="flex space-x-4">
                      {navigation.map((item) => (
                        <a
                          key={item.name}
                          href={item.href}
                          className={classNames(
                            location.pathname === item.href
                              ? 'font-semibold'
                              : 'hover:[text-shadow:_0px_8px_16px_rgb(0_0_0_/_70%)]',
                            'rounded-md px-3 py-2 text-md text-white visited:text-white'
                          )}
                          aria-current={
                            location.pathname === item.href ? 'page' : undefined
                          }
                        >
                          {item.name}
                        </a>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
              {user ? (
                <div className="h-full min-w-56 flex items-center justify-center border-l-2 border-white">
                  <div className="absolute inset-y-0 right-0 flex items-center pr-2 sm:static sm:inset-auto sm:ml-6 sm:pr-0">
                    {/* Profile dropdown */}
                    <Menu as="div" className="relative ml-3 text-white">
                      <Menu.Button className="relative flex rounded-full">
                        <span className="absolute -inset-1.5" />
                        <span className="sr-only">Open user menu</span>
                        <div className="flex items-center justify-center">
                          {user.profile_url ? (
                            <img
                              key={user.profile_url
                                .split('/')
                                .slice(-1)[0]
                                .slice(0, -4)}
                              className="h-8 w-8 rounded-full"
                              src={user.profile_url}
                            />
                          ) : (
                            <div
                              className="flex items-center justify-center h-8 w-8 text-sm rounded-full"
                              style={generateRandomProfileColor(
                                user.first_name + ' ' + user.last_name
                              )}
                            >
                              <span className="indent-[0.1em] tracking-widest">
                                {user.first_name[0] + user.last_name[0]}
                              </span>
                            </div>
                          )}

                          <div className="hidden md:inline ml-4">
                            {user.first_name} {user.last_name}
                          </div>
                          <ChevronDownIcon
                            className="inline h-4 w-4 ml-2"
                            aria-hidden="true"
                          />
                        </div>
                      </Menu.Button>
                      <Transition
                        as={Fragment}
                        enter="transition ease-out duration-100"
                        enterFrom="transform opacity-0 scale-95"
                        enterTo="transform opacity-100 scale-100"
                        leave="transition ease-in duration-75"
                        leaveFrom="transform opacity-100 scale-100"
                        leaveTo="transform opacity-0 scale-95"
                      >
                        <Menu.Items className="absolute right-0 z-50 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                          <Menu.Item>
                            {({ active }) => (
                              <Link
                                to="/auth/profile"
                                className={classNames(
                                  active ? 'bg-gray-100' : '',
                                  'block px-4 py-2 text-sm text-gray-700 visited:text-gray-700'
                                )}
                              >
                                Your Profile
                              </Link>
                            )}
                          </Menu.Item>
                          {user.is_superuser ? (
                            <Menu.Item>
                              {({ active }) => (
                                <Link
                                  to="/admin/dashboard"
                                  className={classNames(
                                    active ? 'bg-gray-100' : '',
                                    'block px-4 py-2 text-sm text-gray-700 visited:text-gray-700'
                                  )}
                                >
                                  Dashboard
                                </Link>
                              )}
                            </Menu.Item>
                          ) : null}
                          <Menu.Item>
                            {({ active }) => (
                              <Link
                                to="/auth/logout"
                                className={classNames(
                                  active ? 'bg-gray-100' : '',
                                  'block px-4 py-2 text-sm text-gray-700 visited:text-gray-700'
                                )}
                              >
                                Sign out
                              </Link>
                            )}
                          </Menu.Item>
                        </Menu.Items>
                      </Transition>
                    </Menu>
                  </div>
                </div>
              ) : (
                <div className="h-full min-w-56 flex items-center justify-center border-l-2 border-white">
                  <div className="absolute inset-y-0 right-0 flex items-center text-white pr-2 sm:static sm:inset-auto sm:ml-6 sm:pr-0">
                    <Link to="/auth/login">Sign in</Link>
                  </div>
                </div>
              )}
            </div>
          </div>

          {user ? (
            <Disclosure.Panel className="sm:hidden">
              <div className="space-y-1 px-2 pb-3 pt-2">
                {navigation.map((item) => (
                  <Disclosure.Button
                    key={item.name}
                    as="a"
                    href={item.href}
                    className={classNames(
                      location.pathname === item.href ? 'font-semibold' : '',
                      'block rounded-md px-3 py-2 text-white visited:text-white font-medium'
                    )}
                    aria-current={location.pathname === item.href ? 'page' : undefined}
                  >
                    {item.name}
                  </Disclosure.Button>
                ))}
              </div>
            </Disclosure.Panel>
          ) : null}
        </>
      )}
    </Disclosure>
  );
}
