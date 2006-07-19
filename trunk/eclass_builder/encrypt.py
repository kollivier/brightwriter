import sys, unittest

def munge(string, pad):
	pad_length = len(pad)
	s = ""
	for i in range(len(string)):
		c = ord(string[i]) ^ ord(pad[i % pad_length])
		s = s + chr(c)
	return s

def encrypt(text):
    crypt = munge(text, 'foobar')
    retval = ""
    for x in crypt:
        retval += "%02X " % ord(x)
    return retval
    
def decrypt(text):
    decrypt = ""
    # make sure we don't add the last space into the result
    chars = text.strip().split(" ")
    for x in chars:
        decrypt += chr(int('0x' + x, 16))
    return munge(decrypt, 'foobar')
    
class EncryptionTests(unittest.TestCase):
    def setUp(self):
        self.testString = "The foo bars"
        self.crypt = "32 07 0A 42 07 1D 09 4F 0D 03 13 01 "
        
    def testEncrypt(self):
        result = encrypt(self.testString)
        self.assertEqual(result, self.crypt)
        
    def testDecrypt(self):
        result = decrypt(self.crypt)
        self.assertEqual(result, self.testString)
        
    def testRoundtrip(self):
        result = decrypt(encrypt(self.testString))
        self.assertEqual(result, self.testString)

def getTestSuite():
    return unittest.makeSuite(EncryptionTests)

if __name__ == '__main__':
    unittest.main()