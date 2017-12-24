from distutils.core import setup

setup(name='feedem',
      version='0.1',
      description="Feed'em",
      author='happz',
      author_email='happz@happz.cz',
      url='',
      packages=[
          'feedem'
      ],
      entry_points={
          'console_scripts': {
              'feed-em = feedem.tool:cli'
          }
      }
      )
