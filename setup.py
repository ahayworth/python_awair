import setuptools

setuptools.setup(
    name="python_awair",
    version="0.0.1",
    url="https://github.com/ahayworth/python_awair",
    author="Andrew Hayworth",
    author_email="ahayworth@gmail.com",
    long_description="asynio client for the Awair GraphQL API",
    license="MIT",
    packages=setuptools.find_packages(),
    install_requires=["aiohttp>=3.4.4", "async_timeout"],
    zip_safe=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Framework :: AsyncIO",
    ]
)
