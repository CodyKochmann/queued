from distutils.core import setup

version = '2019.12.24'

setup(
  name = 'queued',
  packages = ['queued'], # this must be the same as the name above
  version = version,
  install_requires = ["strict_functions","greater_context"],
  description = 'turn python functions into mini high performance microservices',
  author = 'Cody Kochmann',
  author_email = 'kochmanncody@gmail.com',
  url = 'https://github.com/CodyKochmann/queued',
  download_url = 'https://github.com/CodyKochmann/queued/tarball/{}'.format(version),
  keywords = ['queued', 'queue', 'async', 'nonblocking', 'blocking', 'thread', 'multiprocessing', 'parallel', 'message', 'event', 'push', 'microservice', 'microservices', 'performance'],
  classifiers = []
)
