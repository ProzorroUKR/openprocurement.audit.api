from setuptools import setup, find_packages

version = '1.2.9'


def load_requirements(filename):
    requirements = []
    with open(filename) as f:
        for resource in f.readlines():
            if not resource.startswith("git+"):
                requirements.append(resource.strip())
            else:
                res = resource.strip()
                egg = res.split("#egg=")[1]
                requirements.append("@".join([egg, res]))
    return requirements


requires = load_requirements("requirements.txt")
test_requires = requires + [
    'pytest',
    'pytest-xdist<3.0',
    'webtest',
    'freezegun',
    'python-coveralls',
    'coverage',
    'pytest-cov',
]
setup_requires = [
    'pytest-runner',
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
      entry_points=entry_points)
