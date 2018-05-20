from distutils.core import setup

version = '2018.5.20'

setup(
  name = 'queued',
  packages = ['queued'], # this must be the same as the name above
  version = version,
  install_requires = ["strict_functions","greater_context"],
  description = 'simple function decorators that make python functions and generators queued and async for nonblocking operations',
  author = 'Cody Kochmann',
  author_email = 'kochmanncody@gmail.com',
  url = 'https://github.com/CodyKochmann/queued',
  download_url = 'https://github.com/CodyKochmann/queued/tarball/{}'.format(version),
  keywords = ['queued', 'queue', 'async', 'nonblocking', 'blocking', 'thread', 'multiprocessing', 'parallel'],
  classifiers = [],
)
