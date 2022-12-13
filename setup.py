import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="twilio_call_center",
    version="1.0.0",
    author="Paul Kasemir",
    author_email="paul.kasemir@gmail.com",
    description="A django app for dynamic twilio call center",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pkasemir/twilio_call_center",
    project_urls={
        "Bug Tracker": "https://github.com/pkasemir/twilio_call_center/issues",
    },
    install_requires=[
        "apscheduler",
        "django",
        "django_twilio",
        "twilio",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Django",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)

