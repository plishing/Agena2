import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)


from i2clibraries import i2c_hmc5883l

hmc5883l = i2c_hmc5883l.i2c_hmc5883l(1)

hmc5883l.setContinuousMode()
hmc5883l.setDeclination(9,54)


print(hmc5883l)
