from setuptools import setup, find_packages

setup(
    name='springfield',
    packages=['springfield'],
    package_dir={'':'src'},
    version=open('VERSION.txt').read().strip(),
    author='Mike Thornton',
    author_email='six8@devdetails.com',
    url='http://springfield.readthedocs.org',
    download_url='http://github.com/six8/springfield',
    keywords=['orm'],
    license='BSD',
    description='A backend agnostic data modeling entity library',
    classifiers=[
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
        "Development Status :: 3 - Alpha",
    ],
    long_description=open('README.rst').read(),
    install_requires=[
        'anticipate',
    ],
    entry_points={
        'pytest11': [
            'springfield=pytest_springfield',
        ]
    },
)
