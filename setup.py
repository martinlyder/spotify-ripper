#!/usr/bin/env python
# coding=utf-8

from setuptools import setup, find_packages
import os
import io


def create_default_dir():

    if  is_raspberry_pi():
        sudo_username = os.getenv("SUDO_USER")
        home_dir = "/home/" + sudo_username
        default_dir = os.path.normpath(os.path.realpath((os.path.join(home_dir, ".spotify-ripper"))))
    else:
        default_dir = os.path.normpath(os.path.realpath((os.path.join(os.path.expanduser("~"), ".spotify-ripper"))))
    
    
    if not os.path.exists(default_dir):
        print("Creating default settings directory: " +
            default_dir)
        os.makedirs(default_dir.encode("utf-8"))


def _read(fn):
    path = os.path.join(os.path.dirname(__file__), fn)
    return open(path).read()

setup(
    name='spotify-ripper',
    version='2.9.1',
    packages=find_packages(exclude=["tests"]),
    scripts=['spotify_ripper/main.py'],
    include_package_data=True,
    zip_safe=False,

    # Executable
    entry_points={
        'console_scripts': [
            'spotify-ripper = main:main',
        ],
    },

    # Additional data
    package_data={
        '': ['README.rst', 'LICENCE']
    },

    # Requirements
    install_requires=[
        'pyspotify==2.0.5',
        'colorama==0.3.3',
        'mutagen==1.30',
        'requests>=2.3.0',
        'schedule>=0.3.1',
        'spotipy>=2.4.4',
    ],

    # Metadata
    author='James Newell',
    author_email='james.newell@gmail.com',
    description='a small ripper for Spotify that rips Spotify URIs '
                'to audio files',
    license='MIT',
    keywords="spotify ripper mp3 ogg vorbis flac opus acc mp4 m4a",
    url='https://github.com/jrnewell/spotify-ripper',
    download_url='https://github.com/jrnewell/spotify-ripper/tarball/2.9.1',
    classifiers=[
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Capture/Recording',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        "Intended Audience :: Developers",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    long_description=_read('README.rst'),
)

def is_raspberry_pi(raise_on_errors=False):
    """Checks if Raspberry PI.

    :return:
    """
    try:
        with io.open('/proc/cpuinfo', 'r') as cpuinfo:
            found = False
            for line in cpuinfo:
                if line.startswith('Hardware'):
                    found = True
                    label, value = line.strip().split(':', 1)
                    value = value.strip()
                    if value not in (
                        'BCM2708',
                        'BCM2709',
                        'BCM2835',
                        'BCM2836'
                    ):
                        if raise_on_errors:
                            raise ValueError(
                                'This system does not appear to be a '
                                'Raspberry Pi.'
                            )
                        else:
                            return False
            if not found:
                if raise_on_errors:
                    raise ValueError(
                        'Unable to determine if this system is a Raspberry Pi.'
                    )
                else:
                    return False
    except IOError:
        if raise_on_errors:
            raise ValueError('Unable to open `/proc/cpuinfo`.')
        else:
            return False

    return True

create_default_dir()
