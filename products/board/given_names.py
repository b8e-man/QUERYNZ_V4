"""Given-name variants for the near-names pane (ruling 92 (4)): the common
nicknames, short forms and spellings of English given names, and the Māori
forms of them, from public knowledge, as data. Each group is a set of
names that are forms of one another; a name may sit in more than one group
(Chris is Christopher and Christine). Every entry is folded as the search
folds: lower case, macrons dropped (Hēmi is `hemi`).

A variant is a candidate the reader chooses to add to a search, never a
finding that two names are one person, and never a link (plan 4.9: no link
is made by looking; keys/names.py: nicknames are never merged on, a map of
371 filer-stated pairs found nothing beyond chance). Pure: no database."""
from __future__ import annotations

GROUPS: tuple[tuple[str, ...], ...] = (
    # ── men's names, with their Māori forms ──
    ("gareth", "garreth", "garry", "gary", "gaz", "garth"),
    ("william", "bill", "billy", "will", "willy", "willie", "liam", "wiremu", "wi"),
    ("robert", "bob", "bobby", "rob", "robbie", "bert", "ropata"),
    ("richard", "dick", "dicky", "rick", "ricky", "rich", "richie", "rihari", "riki"),
    ("michael", "mike", "mick", "mickey", "micky", "mikey", "mikaere", "mikaera"),
    ("james", "jim", "jimmy", "jamie", "jem", "hamish", "seamus", "hemi"),
    ("john", "jack", "johnny", "jon", "jonny", "hone", "hoani", "tiaki", "sean", "shaun", "shawn", "ian", "iain"),
    ("jonathan", "jon", "jonny", "jonty"),
    ("thomas", "tom", "tommy", "tamati", "tame"),
    ("edward", "ed", "eddie", "eddy", "ted", "teddy", "ned", "eruera"),
    ("anthony", "antony", "tony"),
    ("christopher", "chris", "kit", "topher"),
    ("christian", "chris", "karaitiana"),
    ("patrick", "pat", "paddy", "patariki"),
    ("joseph", "joe", "joey", "hohepa"),
    ("alexander", "alex", "alec", "sandy", "xander", "alastair", "alistair", "alasdair"),
    ("andrew", "andy", "drew", "anaru"),
    ("daniel", "dan", "danny"),
    ("david", "dave", "davey", "davy", "rawiri"),
    ("stephen", "steven", "steve", "stevie", "tipene"),
    ("peter", "pete", "pita", "petera"),
    ("gerald", "gerard", "gerry", "jerry"),
    ("henry", "harry", "hank", "hal", "henare", "hare"),
    ("harold", "harry", "hal"),
    ("charles", "charlie", "chuck", "chas"),
    ("frederick", "frederic", "fred", "freddie", "freddy"),
    ("benjamin", "ben", "benny", "benji", "pene"),
    ("samuel", "sam", "sammy", "hamiora"),
    ("nicholas", "nick", "nicky", "nic", "nico", "nikora"),
    ("matthew", "mathew", "matt", "matty", "matiu"),
    ("timothy", "tim", "timmy", "timoti"),
    ("kenneth", "ken", "kenny"),
    ("ronald", "ron", "ronnie"),
    ("donald", "don", "donnie"),
    ("douglas", "doug", "dougie", "dougal"),
    ("gregory", "greg"),
    ("geoffrey", "jeffrey", "geoff", "jeff"),
    ("leonard", "len", "lenny", "leo"),
    ("lawrence", "laurence", "larry", "laurie"),
    ("raymond", "ray"),
    ("phillip", "philip", "phil", "pip", "piripi"),
    ("terence", "terrence", "terry"),
    ("vincent", "vince", "vinnie"),
    ("walter", "wally", "walt"),
    ("albert", "al", "bert", "bertie"),
    ("alan", "allan", "allen", "al"),
    ("alfred", "alf", "alfie", "fred"),
    ("arthur", "art", "artie"),
    ("bernard", "bernie"),
    ("francis", "frank", "frankie", "fran"),
    ("gabriel", "gabe"),
    ("howard", "howie"),
    ("jacob", "jake"),
    ("joshua", "josh"),
    ("lewis", "louis", "lou"),
    ("levi", "rewi"),
    ("mitchell", "mitch"),
    ("nathaniel", "nathan", "nat", "nate"),
    ("oliver", "ollie", "olly"),
    ("reginald", "reg", "reggie"),
    ("rodney", "rod", "roddy"),
    ("roger", "rog"),
    ("russell", "russ"),
    ("stanley", "stan"),
    ("stuart", "stewart", "stu"),
    ("theodore", "theo", "ted"),
    ("trevor", "trev"),
    ("zachary", "zach", "zack", "zac"),
    ("isaac", "ike", "ihaka"),
    ("moses", "mohi"),
    ("abraham", "abe", "abram", "aperahama"),
    ("mark", "marc", "marcus", "maaka"),
    ("simon", "si", "haimona"),
    ("paul", "paulie", "paora"),
    ("george", "georgie", "hori"),
    ("isaiah", "ihaia"),
    ("josiah", "hohaia"),
    ("aidan", "aiden", "ayden"),
    ("brian", "bryan"),
    ("brendan", "brendon"),
    ("carl", "karl"),
    ("colin", "collin"),
    ("derek", "derrick", "del"),
    ("dominic", "dom"),
    ("graham", "graeme", "grahame"),
    ("glen", "glenn"),
    ("jeremy", "jerry", "jez"),
    ("kevin", "kev"),
    ("malcolm", "mal", "malc"),
    ("martin", "marty"),
    ("neil", "neal", "niall"),
    ("nigel", "nige"),
    ("cameron", "cam"),
    ("jayden", "jaden", "jaiden"),
    ("jason", "jase"),
    ("scott", "scotty"),
    # ── women's names, with their Māori forms ──
    ("elizabeth", "elisabeth", "liz", "lizzie", "lizzy", "beth", "betty", "eliza", "libby", "bess", "bessie", "lisa", "elsie"),
    ("margaret", "maggie", "meg", "peggy", "marge", "margie", "greta", "rita", "margo", "makere"),
    ("katherine", "catherine", "kathryn", "katharine", "kate", "katie", "kathy", "cathy", "kat", "kitty", "cate",
     "katarina", "kataraina"),
    ("kathleen", "kath", "kathy"),
    ("christine", "christina", "chris", "chrissy", "tina", "kirsty", "kirsten"),
    ("patricia", "pat", "patty", "trish", "tricia"),
    ("josephine", "jo", "josie"),
    ("alexandra", "alex", "sandra", "sandy", "lexi"),
    ("samantha", "sam", "sammy"),
    ("nicola", "nicole", "nicky", "nikki", "nic"),
    ("frances", "fran", "frankie"),
    ("abigail", "abby", "abbie", "gail"),
    ("amanda", "mandy"),
    ("barbara", "barb", "babs"),
    ("caroline", "carol", "carrie", "caro", "carolyn"),
    ("deborah", "debra", "debbie", "deb"),
    ("dorothy", "dot", "dottie", "dorothea"),
    ("eleanor", "elinor", "ellie", "nell", "nora"),
    ("helen", "helena", "ellen", "nell"),
    ("jennifer", "jen", "jenny", "jenni"),
    ("jessica", "jess", "jessie"),
    ("judith", "judy", "jude"),
    ("louise", "louisa", "lou", "ruihi"),
    ("madeleine", "madeline", "maddie", "maddy"),
    ("mary", "molly", "polly", "mae", "mere", "meri"),
    ("maria", "marie", "maraea"),
    ("marianne", "maryanne", "mereana"),
    ("anne", "ann", "annie", "anna", "ani"),
    ("hannah", "hanna", "hana"),
    ("sarah", "sara", "sally", "sal", "hera"),
    ("rachel", "rachael", "rach", "rahera"),
    ("rebecca", "becky", "becca", "bec", "ripeka"),
    ("martha", "marty", "mata"),
    ("victoria", "vicky", "vicki", "tori", "wikitoria"),
    ("susan", "sue", "susie", "suzie", "huhana"),
    ("suzanne", "susanne", "sue", "suzie"),
    ("rosemary", "rose", "rosie"),
    ("theresa", "teresa", "terri", "tess", "tessa"),
    ("virginia", "ginny"),
    ("jacqueline", "jackie", "jacqui", "jacquie"),
    ("joanne", "joanna", "jo", "joan"),
    ("kimberley", "kimberly", "kim"),
    ("lynette", "lyn", "lynn", "lynne"),
    ("megan", "meg"),
    ("melissa", "mel", "missy"),
    ("melanie", "mel"),
    ("michelle", "michele", "shelley", "shelly"),
    ("natalie", "natalia", "nat"),
    ("penelope", "penny", "pen"),
    ("philippa", "phillipa", "pippa", "pip"),
    ("sophia", "sophie"),
    ("stephanie", "steph"),
    ("valerie", "val"),
    ("isabella", "isabel", "isobel", "izzy", "bella"),
    ("julia", "julie", "jules"),
    ("lucy", "lucinda", "lucia"),
    ("olivia", "liv", "livvy"),
    ("tracey", "tracy", "tracie"),
    ("georgina", "georgie", "gina"),
    ("jane", "janey", "jayne"),
    ("emma", "em", "emmy"),
    ("esther", "hetere"),
    ("ngaire", "ngaere"),
)


def variants_of(name: str) -> frozenset:
    """Every name that shares a group with `name` (folded), itself excluded."""
    n = (name or "").strip().lower()
    return frozenset(x for g in GROUPS if n in g for x in g) - {n}


def levenshtein(a: str, b: str) -> int:
    """The edit distance between two words: insertions, deletions and substitutions."""
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


#: why a held name is offered, in the pane's words
COMMON, PREFIX, ONE_APART = "a common form of the name", "the same first three letters", "one letter apart"


def why_near(typed: str, held: str):
    """Why `held` is offered as a variant of `typed`, or None: a form in
    GROUPS, the same first three letters, or one edit apart. An initial
    (one letter) is never offered, and neither is the name itself."""
    t, h = typed.lower(), held.lower()
    if h == t or len(h) < 2:
        return None
    if h in variants_of(t):
        return COMMON
    if len(t) >= 3 and h[:3] == t[:3]:
        return PREFIX
    if levenshtein(t, h) == 1:
        return ONE_APART
    return None
