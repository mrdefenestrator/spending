import pytest


@pytest.fixture
def sample_ofx(tmp_path):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<?OFX OFXHEADER="200" VERSION="220"?>
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKACCTFROM>
          <ACCTID>1234567890</ACCTID>
        </BANKACCTFROM>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20240115120000</DTPOSTED>
            <TRNAMT>-42.50</TRNAMT>
            <FITID>20240115001</FITID>
            <NAME>WHOLE FOODS MARKET #10234</NAME>
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>CREDIT</TRNTYPE>
            <DTPOSTED>20240116120000</DTPOSTED>
            <TRNAMT>1500.00</TRNAMT>
            <FITID>20240116001</FITID>
            <NAME>DIRECT DEPOSIT ACME CORP</NAME>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>"""
    path = tmp_path / "test.ofx"
    path.write_text(content)
    return path


@pytest.fixture
def sample_ofx_with_meta(tmp_path):
    content = """<?xml version="1.0" encoding="UTF-8"?>
<?OFX OFXHEADER="200" VERSION="220"?>
<OFX>
  <SIGNONMSGSRSV1>
    <SONRS>
      <STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>
      <DTSERVER>20240115120000</DTSERVER>
      <LANGUAGE>ENG</LANGUAGE>
      <FI><ORG>Chase</ORG><FID>10898</FID></FI>
    </SONRS>
  </SIGNONMSGSRSV1>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKACCTFROM>
          <ACCTID>1234567890</ACCTID>
          <ACCTTYPE>CHECKING</ACCTTYPE>
        </BANKACCTFROM>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20240115120000</DTPOSTED>
            <TRNAMT>-42.50</TRNAMT>
            <FITID>20240115001</FITID>
            <NAME>WHOLE FOODS</NAME>
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>"""
    path = tmp_path / "test_meta.ofx"
    path.write_text(content)
    return path


@pytest.fixture
def sample_csv(tmp_path):
    content = """Transaction Date,Post Date,Description,Category,Type,Amount
01/15/2024,01/16/2024,WHOLE FOODS MARKET #10234,Groceries,Sale,-42.50
01/16/2024,01/17/2024,DIRECT DEPOSIT ACME CORP,Income,Payment,1500.00
01/16/2024,01/17/2024,COFFEE SHOP,Food & Drink,Sale,-5.00
01/16/2024,01/17/2024,COFFEE SHOP,Food & Drink,Sale,-5.00
"""
    path = tmp_path / "test.csv"
    path.write_text(content)
    return path
