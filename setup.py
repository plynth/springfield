from subprocess import check_call
import sys
from setuptools import setup

if sys.argv[-1] in ('build', 'publish'):
    check_call(
        'rst_include include ./_README.rst ./README.rst', shell=True)
    check_call('python setup.py sdist bdist_wheel --universal', shell=True)
    if sys.argv[-1] == 'publish':
        check_call('twine check dist/*', shell=True)
        check_call('twine upload dist/*', shell=True)
    sys.exit()


setup(
    name='springfield',
    packages=['springfield', 'pytest_springfield'],
    package_dir={'': 'src'},
    version=open('VERSION.txt').read().strip(),
    author='Mike Thornton',
    author_email='six8@devdetails.com',
    url='http://springfield.readthedocs.org',
    download_url='http://github.com/plynth/springfield',
    keywords=['orm'],
    license='BSD',
    description='A backend agnostic data modeling entity library',
    classifiers=[
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Topic :: Software Development :: Libraries :: Python Modules",
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
    ],
    long_description=open('README.rst').read(),
    long_description_content_type='text/x-rst',
    install_requires=[
        'anticipate>=0.9.1',
        'six>=1.9.0',
    ],
    entry_points={
        'pytest11': [
            'springfield=pytest_springfield',
        ]
    },
)
