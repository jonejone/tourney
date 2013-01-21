import urllib2
from BeautifulSoup import BeautifulSoup
from HTMLParser import HTMLParseError


class PDGARanking:
    def __init__(self, number):
        self.number = number
        self.url = 'http://www.pdga.com/player-stats?PDGANum=%s' % number
        self.response = None
        self.load()
        self.parse()

    def load(self):
        self.response = urllib2.urlopen(
            self.url).read()

    def parse(self):
        try:
            soup = BeautifulSoup(self.response)

            # Get current rating
            p = soup.find('p', attrs={'class':'current-rating'})
            rating = p.contents[1].replace(' ', '')

            # Get the name also
            h1 = soup.find('h1', attrs={'class':'page-title'})
            name = h1.contents[0].split('#')[0]

            # And location
            location = soup.find('p',
                attrs={'class':'location'}).contents[1]
            
        except HTMLParseError, e:
            self.rating = None
            self.name = None
        except AttributeError:
            self.rating = None
            self.name = None
        else:
            self.rating = rating
            self.name = name
            self.location = location


if __name__ == '__main__':
    import sys
    num = sys.argv[1]
    rank = PDGARanking(num)
    print rank.rating
    print rank.name

