from distill.helpers import CaseInsensitiveDict, url_decode

try:
    import testtools as unittest
except ImportError:
    import unittest


class TestHelpers(unittest.TestCase):
    def test_insensitive_dict(self):
        dic = CaseInsensitiveDict()
        dic['Foo'] = 'Bar'
        self.assertEqual(dic['foo'], 'Bar')
        dic['foo'] = 'Baz'
        self.assertEqual(dic['Foo'], 'Baz')
        del dic['foo']
        self.assertNotIn('Foo', dic)
        dic['Bar'] = 'Foo'
        dic['Foo'] = 'Bar'
        self.assertEqual(len(dic), 2)
        self.assertEqual(dic.get('Baz', 'Bar'), 'Bar')
        dic.setdefault('Baz', 'Bar')
        self.assertEqual(dic['Baz'], 'Bar')
        dic.setdefault('Baz', 'Foo')
        self.assertNotEqual(dic['Baz'], 'Foo')
        self.assertEqual(dic, dic.copy())
        self.assertEqual(dict(dic.items()), {"Foo": "Bar", "Bar": "Foo", "Baz": "Bar"})
        self.assertEqual(dict([(k, v) for k, v in dic.iteritems()]),
                         {"Foo": "Bar", "Bar": "Foo", "Baz": "Bar"})
        for k in dic:
            self.assertEqual(dic[k], {"Foo": "Bar", "Bar": "Foo", "Baz": "Bar"}[k])

        for k in dic.keys():
            self.assertIn(k, ["Foo", "Bar", "Baz"])

    def test_urldecdoe(self):
        url = "%7B%22Foo%22%3A+%22foo+bar%22%7d"
        self.assertEqual(url_decode(url), '{"Foo": "foo bar"}')