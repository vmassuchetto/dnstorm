from setuptools import setup, find_packages

install_required = [l.strip() for l in open("requirements.txt", "r")]

metadata = {
    'name': 'DNStorm',
    'version': '1.0',
    'description': 'A decision-making Django project focused in alternatives generation.',
    'url': "https://github.com/vmassuchetto/dnstorm",
    'author': 'Vinicius Massuchetto',
    'author_email': 'vmassuchetto@gmail.com',
    'platforms': ['linux'],
    'packages': find_packages(),
    'install_required': install_required,
}

if __name__ == '__main__':
    setup(**metadata)
