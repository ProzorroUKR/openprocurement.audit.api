from setuptools import setup, find_packages

version = '1.2.3'

requires = [
    'pyramid<1.10.0',
    'schematics<2.0.0',
    'pymongo>=3.10.1<4',
    'cornice==1.2.0.dev0',
    'barbecue',
    'chaussette',
    'cornice',
    'gevent',
    'iso8601',
    'isodate',
    'zope.component',
    'zope.configuration',
    'esculator',
    'pycrypto',
    'libnacl',
    'pbkdf2',
    'six',
    'PyNaCl<2',
    'pytz',
    'pyramid_exclog',
    'jsonpatch==1.14-dp',
    'rfc6266==0.0.6',
    'openprocurement_client==2.1.1dp',
    'standards>=1.0.22',
]
test_requires = requires + [
    'pytest',
    'pytest-xdist',
    'webtest',
    'freezegun',
    'python-coveralls',
    'coverage',
    'pytest-cov',
]
setup_requires = [
    'pytest-runner',
    'setuptools==33.1.1',
    'six',
]
dependency_links = [
    "https://github.com/ProzorroUKR/openprocurement.client.python/tarball/2.1.1dp#egg=openprocurement_client-2.1.1dp",
    "https://github.com/ProzorroUKR/esculator/tarball/master#egg=esculator",
    "https://github.com/ProzorroUKR/dateorro/tarball/master#egg=dateorro",
    "https://github.com/ProzorroUKR/barbecue/tarball/master#egg=barbecue",
    "https://github.com/ProzorroUKR/cornice/tarball/1.2.0.dev0#egg=cornice-1.2.0.dev0",
    "https://github.com/ProzorroUKR/rfc6266/tarball/0.0.6#egg=rfc6266-0.0.6",
    "https://github.com/ProzorroUKR/python-json-patch/tarball/1.14-dp#egg=jsonpatch-1.14-dp",
]


entry_points = {
    'paste.app_factory': [
        'main = openprocurement.audit.api.app:main'
    ],
    'openprocurement.audit.api.plugins': [
        'api = openprocurement.audit.api:includeme',
        'monitoring = openprocurement.audit.monitoring:includeme',
        'inspection = openprocurement.audit.inspection:includeme',
        'request = openprocurement.audit.request:includeme',
    ]
}

setup(name='openprocurement.audit.api',
      version=version,
      long_description=open("README.rst").read(),
      classifiers=[
          "Programming Language :: Python",
      ],
      author='RaccoonGang',
      author_email='info@raccoongang.com',
      license='Apache License 2.0',
      url='https://github.com/ProzorroUKR/openprocurement.audit.api',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['openprocurement', 'openprocurement.audit'],
      include_package_data=True,
      package_data={'': ['data/*.json']},
      zip_safe=False,
      install_requires=requires,
      setup_requires=setup_requires,
      tests_require=test_requires,
      extras_require={'test': test_requires},
      dependency_links=dependency_links,
      entry_points=entry_points)
