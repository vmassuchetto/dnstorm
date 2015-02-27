from setuptools import setup, find_packages
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt')
reqs = [str(ir.req) for ir in install_reqs]

metadata = {
    'name': 'dnstorm',
    'version': '1.0',
    'description': 'A decision-making Django project focused in alternatives generation.',
    'url': "https://github.com/vmassuchetto/dnstorm",
    'author': 'Vinicius Massuchetto',
    'author_email': 'vmassuchetto@gmail.com',
    'platforms': ['linux'],
    'packages': find_packages(),
    'install_requires': reqs,
    'zip_safe': True
}

if __name__ == '__main__':
    setup(**metadata)
