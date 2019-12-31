from cards import Suit, Card, Hand

from itertools import chain
from random import shuffle
from queue import Queue


class Game:
    """
    Object that represents an entire game of 500 - multiple rounds until a
    player or team reaches 500 points, or a single round, depending on the
    chosen game type.

    This object stores information about the game including the players, the
    type, the score, the deck.

    The game controller should create an instance of this when it starts and
    then fill out attributes using methods with user input before starting a
    round.

    !! Probably should contain the current round as an attribute so that it
    can be accessed by the game controller to interpret clicks?

    !! We might need to make separate scoring and playing teams to be able to
    handle 3 and 5 player games? idk can deal with later probs
    """
    def __init__(self):
        """
        An instance of Game should be initialised when a new session is
        started, before any user input.
        """
        # game_type can be "single" or "500", specified with user input in
        # initGame method
        self.game_type = None
        # player_count can be 3, 4, 5 or 6, specified with user input in
        # initPlayers method
        self.player_count = None
        # players is a list of players in the order they play, each player
        # is an instance of class Player
        self.players = None
        # teams is a list of lists of teams and their members, specified with
        # user input in the initPlayers method
        self.teams = None
        # deck is a list of cards, determined by the number of players
        self.deck = []
        # the current round stores information about the current round for
        # user by the game controller
        self.current_round = None
        # score should contain information about the overall score, should be
        # a list of tuples with the player name (might be easier than using a
        # whole player object idk). Other option is to store the scores within
        # the player objects and just retrieve that, not sure which is easier.
        self.score = []

    def initGame(self, game_type="single"):
        """
        Call this method from the game controller with the user's input of the
        game type to set the game type when a new game is started.
        :param game_type: "single" or "500"
        """
        if game_type == "500" or game_type == "single":
            self.game_type = game_type
        else:
            raise Exception("Invald type parameter for game.")

    def initPlayers(self, player_count=4, players=None, teams=None):
        """
        Call this method with the user's input of the number of players, a list
        of players and a list of lists defining teams to set the players and
        teams to set these for the game. This should be called within the game
        controller when starting a new game.
        :param player_count: an int with the number of players
        :param players: a list of objects of type Player
        :param teams: a list of lists, where each inner list is a list of
        strings, each representing a member of that team
        """
        self.player_count = player_count

        self.players = players
        # if player names not entered, use these defaults:
        if not self.players:
            self.players = [Player("1", True)] + [Player(str(num)) for num in range(2, player_count + 1)]
        if len(self.players) != player_count:
            raise Exception("Number of player names entered does not match "
                            "player count.")

        self.teams = teams
        # if teams not entered, use these defaults:
        if not self.teams:
            if player_count == 3:
                self.teams = [["1", "2", "3"]]
            elif player_count == 4:
                self.teams = [["1", "3"], ["2", "4"]]
            elif player_count == 5:
                self.teams = [["1", "2", "3", "4", "5"]]
            elif player_count == 6:
                self.teams =[["1", "3", "5"], ["2", "4", "6"]]

        # need to catch invalid teams here, but it is a bit difficult, will do
        # this another time
        # TODO: catch invalid teams

    def startRound(self):
        """
        This should start a round of 500 (ie. bidding, 10 tricks and
        winner determination). It should be called by the game controller once
        and then if it is in 500 mode it should be called again when a round
        finishes without 500 being reached by any teams.

        It should initialise an instance of Round and save it as
        self.current_round so that it can be accessed by the game controller
        to handle clicks when needed.
        """

        # May need to sanitise deck here as individual cards would have been
        # assigned bower suits and trump values that would need to be changed.
        # Or could just init deck again every time before startRound is called.

        # -- yes just init the deck each time it should be quick

        self.current_round = Round(self.players, self.player_count, self.teams)

        self.current_round.initDeck()

        self.current_round.dealCards()

        # create a queue of objects (1 x Bidding round, 1 x Kitty, 10 x Tricks,
        # 1 x Score) that that will be popped, saved, actioned and deleted as
        # the round progresses. The type of object will determine the action
        # that needs to be taken in response to a click.
        self.current_round.createRoundQueue()

        # pop the first item of the queue, save and begin actioning
        self.current_round.startRound()

        # !! The rest of the stages of the round need to be initiated by user
        # input, and using the current round's queue

    def displayResults(self):
        """
        Not sure if this will be needed or how we will determine when to
        display the overall score.
        """
        # TODO: work out how to display end of game results
        raise NotImplementedError


class Player:
    """
    An object representing a player which simply stores information about
    their name as a string and whether they are human as a boolean.

    More information such as the tricks they have won in the current round may
    need to be added, not sure.
    """
    def __init__(self, name, is_human=False):
        self.name = name
        self.is_human = is_human


class Round:
    """
    A round includes a round of bidding, 10 tricks, and the determination of
    the winner and point allocation.
    """
    def __init__(self, players, player_count, teams):
        # an ordered list of players, each of type Player.
        self.players = players
        # an int representing the number of players
        self.player_count = player_count
        # a list of lists where each inner list contains strings, representing
        # the names of players in that team
        self.teams = teams
        # a list of objects of type Hand, corresponding to the players in
        # self.players and in the same order
        self.hands = []
        # an object of type Hand that contains the cards in the kitty
        self.kitty = None
        # the deck of cards, a list containing objects of type Card
        self.deck = []
        # queue of objects to be actioned in this round
        self.stage_queue = Queue()
        # stage in progress, type is either BiddingRound, Trick or something with scoring
        self.stage_in_progress = None
        # winning bid of bidding round, type is bid
        self.winning_bid = None
        # completed tricks, a list of tricks that have been completed
        self.completed_tricks = []

    def initDeck(self):
        """
        Initialises self.deck with the appropriate deck of cards for the
        number of players. self.deck is a list of cards, each of type Card.
        This should be called by the game controller only once at the start
        of each game after the number of players is set.
        """
        # first decide number of number cards needed of each suit

        # 16 picture cards + joker, number cards have card values 2-13, picture
        # cards have card values 14-17, joker has card value 18

        red_cards = None
        black_cards = None

        while not red_cards or not black_cards:
            if self.player_count == 3:
                # need 33 cards total, so 16 number cards, red 7-10, black 7-10
                red_cards = list(chain(range(7, 11), range(14, 18)))
                black_cards = list(chain(range(7, 11), range(14, 18)))
            elif self.player_count == 4:
                # need 43 cards in total, so 26 number cards, red 4-10, black 5-10
                red_cards = list(chain(range(4, 11), range(14, 18)))
                black_cards = list(chain(range(5, 11), range(14, 18)))
            elif self.player_count == 5:
                # need 53 cards in total, full regular deck (2-10)
                red_cards = list(chain(range(2, 11), range(14, 18)))
                black_cards = list(chain(range(2, 11), range(14, 18)))
            elif self.player_count == 6:
                # need 63 cards in total, so 46 number cards, red 2-13, black 3-13
                red_cards = list(range(2, 18))
                black_cards = list(range(3, 18))
            else:
                raise Exception("Please choose a number of players between 3 and 6.")

        # create notrumps suit and cards (for joker and no-trumps bids)
        notrumps = Suit("NT", 5)
        self.deck.append(Card(notrumps, 18))

        # create suits and cards and add to deck
        hearts = Suit("H", 4)
        self.deck.extend([Card(hearts, val) for val in red_cards])
        diamonds = Suit("D", 3)
        self.deck.extend([Card(diamonds, val) for val in red_cards])
        clubs = Suit("C", 2)
        self.deck.extend([Card(clubs, val) for val in black_cards])
        spades = Suit("S", 1)
        self.deck.extend([Card(spades, val) for val in black_cards])

    def dealCards(self):
        """
        Deal cards to players and kitty, adding cards to self.hands and
        self.kitty, also setting player attribute of cards.
        :return:
        """
        # shuffle deck
        shuffle(self.deck)

        # next, create hands
        for player in self.players:
            # get cards dealt to single player
            dealt_cards = self.deck[-10:]
            # remove dealt cards from deck
            del self.deck[-10:]
            # set player attribute of cards
            for card in dealt_cards:
                card.assignToPlayer(player)
            # add dealt hand to list of hands
            self.hands.append(Hand(dealt_cards, player))
        # deal cards to kitty
        self.kitty = Hand(self.deck, Player("kitty"))

        for hand in self.hands:
            hand.printFullHand()

        self.kitty.printFullHand()

    def createRoundQueue(self):
        """
        Create a queue of objects that need to be actioned in one round.
        1 x bidding round, 10 x tricks, 1 x score determination
        """
        # initialise queue of round's stages
        self.stage_queue = Queue()

        # add bidding round stage
        self.stage_queue.put(BiddingRound(self.player_count, self.players))
        # add trick stages
        for _ in range(0, 10):
            self.stage_queue.put(Trick())

        # TODO: add something about scoring here idk


    def startRound(self):
        """
        Get first element (stage) of round queue and set this as current stage.

        Stage will then be implemented in continueRound.
        """

        # first element should be a bidding round
        self.stage_in_progress = self.stage_queue.get()

    def continueRound(self):
        """
        Get in progress round stage and continue to action using received user
        input.
        """
        # TODO: fill this in - while loop for round then while loops for stages
        # while

    def implementBiddingResults(self):
        """
        1. Assign trumps to cards.
        2. Assign roles to players.
        3. Give winner kitty and throw out cards.
        """
        # TODO: implement implementBiddingResults
        raise NotImplementedError

    def displayResults(self):
        """
        Display the results of a single round.
        """
        # TODO: implement displayResults
        raise NotImplementedError


class Bid:
    """
    Bid is used to represent a single bid by a player.
    """
    def __init__(self, suit, number, player):
        self.suit = suit
        self.number = number
        self.player = player
        if number == 0:
            self.bid_name = "Pass"
            self.is_pass = True
        else:
            self.bid_name = "{}{}".format(self.number, self.suit)
            self.is_pass = False

    def __repr__(self):
        """
        Define how bids are represented as strings.
        """
        return self.bid_name

    def __lt__(self, other):
        """
        Define how bids are ordered.
        """
        return self.number < other.number or \
               (self.number == other.number and self.suit < other.suit) or \
               self.is_pass


class BiddingRound:
    """
    One round of bidding, lasts until only one player is remaining.
    """
    def __init__(self, player_count, players):
        # any first bid above this default is valid
        self.winning_bid = Bid(Suit("NT", 5), 5, None)
        # is the bidding round complete?
        self.complete = False
        # number of players that have not passed
        self.remaining_player_count = player_count
        # list of players that have not passed
        self.remaining_players = players
        # index used to cycle through players in order
        self.current_player_index = 0

    def addBid(self, bid):
        if bid > self.winning_bid:
            self.winning_bid = bid
            return 1
        elif bid.is_pass:
            self.remaining_players.remove(bid.player)
            self.remaining_player_count -= 1
            if self.remaining_players == 1:
                self.complete = True
            return 1
        else:
            print("Bid too low, try again.")
            return 0

    def getWinningBid(self):
        if self.complete:
            return self.winning_bid


class Trick:
    """
    An object representing a trick that is either in progress or has been
    won by a particular player.
    """
    def __init__(self):
        raise NotImplementedError

    def addCardToTrick(self, card):
        raise NotImplementedError

    def setTrickWinner(self):
        raise NotImplementedError


a = Player("A")
b = Player("B")
c = Player("C")
d = Player("D")

round1 = Round([a, b, c, d], 4, [["A", "B"], ["C", "D"]])

round1.initDeck()
round1.dealCards()



