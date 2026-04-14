from models import Admin, YahooAccount, Alias


def test_create_admin(db_session):
    admin = Admin(username="admin", password_hash="hashed")
    db_session.add(admin)
    db_session.commit()
    assert db_session.query(Admin).count() == 1
    assert db_session.query(Admin).first().username == "admin"


def test_create_yahoo_account(db_session):
    account = YahooAccount(email="user@yahoo.com", imap_password="encrypted")
    db_session.add(account)
    db_session.commit()
    assert db_session.query(YahooAccount).first().email == "user@yahoo.com"
    assert db_session.query(YahooAccount).first().status == "normal"


def test_create_alias_with_relationship(db_session):
    account = YahooAccount(email="user@yahoo.com", imap_password="encrypted")
    db_session.add(account)
    db_session.commit()

    alias = Alias(alias_email="alias1@yahoo.com", account_id=account.id)
    db_session.add(alias)
    db_session.commit()

    assert alias.account.email == "user@yahoo.com"
    assert len(account.aliases) == 1
    assert account.aliases[0].alias_email == "alias1@yahoo.com"


def test_alias_enabled_default_true(db_session):
    account = YahooAccount(email="user@yahoo.com", imap_password="encrypted")
    db_session.add(account)
    db_session.commit()

    alias = Alias(alias_email="alias1@yahoo.com", account_id=account.id)
    db_session.add(alias)
    db_session.commit()
    assert alias.enabled is True


def test_cascade_delete_account_removes_aliases(db_session):
    account = YahooAccount(email="user@yahoo.com", imap_password="encrypted")
    db_session.add(account)
    db_session.commit()

    alias = Alias(alias_email="alias1@yahoo.com", account_id=account.id)
    db_session.add(alias)
    db_session.commit()

    db_session.delete(account)
    db_session.commit()
    assert db_session.query(Alias).count() == 0
