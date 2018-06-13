from .option_query import *


class Option(object):
    """
    This class represents a option spread object
    """

    def __init__(self, name=None):
        self.name = name
        self.cols = ['symbol',
                     'expiration',
                     'quote_date',
                     'bid',
                     'ask',
                     'mark',
                     'delta',
                     'gamma',
                     'theta',
                     'vega',
                     'rho'
                     ]


class Single(Option):
    """
    This class simulates a single option position. Either a call or put of an underlying asset
    """

    def __init__(self, **params):
        super(Single, self).__init__('Single')
        self.option_type = params.pop('option_type', 'c')

    def __call__(self, data):
        # get spread params from user or set default if not given
        chains = OptionQuery(data).option_type(self.option_type).fetch()
        chains['mark'] = (chains['bid'] + chains['ask']) / 2
        chains = chains.set_index('quote_date', drop=False)

        return chains.loc[:, chains.columns.isin(self.cols)]


class Vertical(Option):
    """
    The vertical spread is an option spread strategy whereby the
    option trader purchases a certain number of options and simultaneously
    sell an equal number of options of the same class, same underlying security,
    same expiration date, but at a different strike price.
    """

    def __init__(self, **params):
        super(Vertical, self).__init__('Vertical')

        # get spread params from user or set default if not given
        self.option_type = params.pop('option_type', 'c')
        self.width = params.pop('width', 2)

        if not self.width > 0:
            raise ValueError("Width cannot be less than 0")

    def __call__(self, data):
        # here we get all the option chains based on option type
        chains = OptionQuery(data).option_type(self.option_type).fetch()

        chains['strike_key'] = chains['strike'] + (self.width * self.option_type.value[1])

        # shift only the strikes since this is a vertical spread,
        # we create a join key (strike_key) to join on
        chains['strike_key'] = chains['strike'] + (self.width * self.option_type.value[1])
        left_keys = ['quote_date', 'expiration', 'option_type', 'strike_key']
        right_keys = ['quote_date', 'expiration', 'option_type', 'strike']

        # here we do a self join to the table itself joining by strike key, essentially we are
        # shifting the strikes to create the vertical spread
        chains = chains.merge(chains, left_on=left_keys, right_on=right_keys,
                              suffixes=('', '_shifted'))

        # create the strategy symbol that represents this spread
        chains['symbol'] = chains['symbol'] + '-' + chains['symbol_shifted']

        # Calculate the spread's bid and ask prices and
        chains['bid'] = chains['bid'] - chains['ask_shifted']
        chains['ask'] = chains['ask'] - chains['bid_shifted']
        chains['mark'] = round((chains['bid'] + chains['ask']) / 2, 2)

        for greek in ['delta', 'theta', 'gamma', 'vega', 'rho']:
            if greek in chains.columns:
                chains[greek] = chains[greek] - chains[greek + "_shifted"]

        chains = chains.set_index('quote_date', drop=False)
        return chains.loc[:, chains.columns.isin(self.cols)]


class IronCondor(Option):
    """
    The iron condor is an option trading strategy utilizing two vertical spreads
    a put spread and a call spread with the same expiration and four different strikes.
    """

    def __init__(self, option_type, width, c_width, p_width):
        super(IronCondor, self).__init__('Iron Condor')
        self.option_type = option_type
        self.width = width
        self.c_width = c_width
        self.p_width = p_width

    def __call__(self, data):

        if self.width <= 0 or self.c_width <= 0 or self.p_width <= 0:
            raise ValueError("Widths cannot be less than or equal 0")


class CoveredStock(Option):

    def __init__(self, data):
        super(CoveredStock, self).__init__(data)

    def __call__(self, data):
        pass


class Calender(Option):

    def __init__(self, data, width):
        super(Calender, self).__init__(data)
        self.width = width

    def __call__(self, data):
        pass


class ShortCallSpread(Option):

    def __init__(self, data, width):
        super(ShortCallSpread, self).__init__(data)
        self.width = width


class LongPutSpread(Option):

    def __init__(self, data, width):
        super(LongPutSpread, self).__init__(data)
        self.width = width


class ShortPutSpread(Option):

    def __init__(self, data, width):
        super(ShortPutSpread, self).__init__(data)
        self.width = width


class LongIronCondor(Option):

    def __init__(self, data, width, width_c, width_p):
        super(LongIronCondor, self).__init__(data)
        self.width = width
        self.width_c = width_c
        self.width_p = width_p


class ShortIronCondor(Option):

    def __init__(self, data, width, width_c, width_p):
        super(ShortIronCondor, self).__init__(data)
        self.width = width
        self.width_c = width_c
        self.width_p = width_p
