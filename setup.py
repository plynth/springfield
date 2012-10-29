from distutils.core import setup

def main():

    setup(
        name = 'springfield',
        packages=['springfield'],
        package_dir = {'':'src'},
        version = open('VERSION.txt').read().strip(),
        author='Mike Thornton',
        author_email='six8@devdetails.com',
        # url='http://springfield.rtfd.org',
        download_url='http://github.com/six8/springfield',
        keywords=['orm'],
        license='MIT',
        description='A backend agnostic data modeling entity library',
        classifiers = [
            "Programming Language :: Python",
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
        long_description=open('README.rst').read(),
        install_requires = [
            'anticipate',
        ]
    )

if __name__ == '__main__':
    main()