import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="webgo",
    version="0.13.0",
    author="yixuan",
    author_email="yixuan.coder@gmail.com",
    description="A micro web framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/1xuan/webgo",
    license='MIT',
    packages=['webgo'],
    install_requires=['webob'],
    entry_points={
        'console_scripts': [
            'webgo=webgo.wsgiserver:serving',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
