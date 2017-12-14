from distutils.core import setup
setup(
  name = 'queued',
  packages = ['queued'], # this must be the same as the name above
  version = '2017.11.21',
  install_requires = ["strict_functions"],
  description = 'simple function decorators that make python functions and generators queued and async for nonblocking operations',
  author = 'Cody Kochmann',
  author_email = 'kochmanncody@gmail.com',
  url = 'https://github.com/CodyKochmann/queued',
  download_url = 'https://github.com/CodyKochmann/queued/tarball/2017.12.14',
  keywords = ['queued', 'queue', 'async', 'nonblocking', 'blocking', 'thread', 'multiprocessing', 'parallel'],
  classifiers = [],
)
