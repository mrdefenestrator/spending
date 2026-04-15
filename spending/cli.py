import click
from sqlalchemy import create_engine

from spending.models import metadata
from spending.repository.accounts import (
    add_account,
    delete_account,
    edit_account,
    get_account_by_id,
    list_accounts,
)
from spending.repository.categories import (
    add_category,
    delete_category,
    edit_category,
    list_categories,
    seed_categories,
)


@click.group()
@click.option("--db", default="spending.db", help="Path to SQLite database")
@click.pass_context
def cli(ctx, db):
    """Spending tracker CLI."""
    ctx.ensure_object(dict)
    engine = create_engine(f"sqlite:///{db}")
    metadata.create_all(engine)
    ctx.obj["engine"] = engine
    with engine.connect() as conn:
        seed_categories(conn, "configs/categories.yaml")


@cli.group()
def accounts():
    """Manage accounts."""


@accounts.command("list")
@click.pass_context
def accounts_list(ctx):
    """List all accounts."""
    with ctx.obj["engine"].connect() as conn:
        accts = list_accounts(conn)
    if not accts:
        click.echo("No accounts found.")
        return
    for a in accts:
        click.echo(
            f"  [{a['id']}] {a['name']} ({a['institution']}, {a['account_type']})"
        )


@accounts.command("add")
@click.option("--name", required=True)
@click.option("--institution", required=True)
@click.option(
    "--type",
    "account_type",
    required=True,
    type=click.Choice(["checking", "savings", "credit_card"]),
)
@click.pass_context
def accounts_add(ctx, name, institution, account_type):
    """Add a new account."""
    with ctx.obj["engine"].connect() as conn:
        add_account(conn, name=name, institution=institution, account_type=account_type)
    click.echo(f"Added account: {name}")


@accounts.command("edit")
@click.argument("account_id", type=int)
@click.option("--name")
@click.option("--institution")
@click.option("--type", "account_type")
@click.pass_context
def accounts_edit(ctx, account_id, name, institution, account_type):
    """Edit an account."""
    with ctx.obj["engine"].connect() as conn:
        edit_account(
            conn,
            account_id,
            name=name,
            institution=institution,
            account_type=account_type,
        )
    click.echo(f"Updated account {account_id}")


@accounts.command("delete")
@click.argument("account_id", type=int)
@click.pass_context
def accounts_delete(ctx, account_id):
    """Delete an account."""
    with ctx.obj["engine"].connect() as conn:
        acct = get_account_by_id(conn, account_id)
        if not acct:
            click.echo(f"Account {account_id} not found.")
            return
        delete_account(conn, account_id)
    click.echo(f"Deleted account {account_id}")


@cli.group()
def categories():
    """Manage categories."""


@categories.command("list")
@click.pass_context
def categories_list(ctx):
    """List all categories."""
    with ctx.obj["engine"].connect() as conn:
        cats = list_categories(conn)
    for c in cats:
        click.echo(f"  [{c['id']}] {c['name']} (order: {c['sort_order']})")


@categories.command("add")
@click.option("--name", required=True)
@click.option("--sort-order", required=True, type=int)
@click.pass_context
def categories_add(ctx, name, sort_order):
    """Add a new category."""
    with ctx.obj["engine"].connect() as conn:
        add_category(conn, name=name, sort_order=sort_order)
    click.echo(f"Added category: {name}")


@categories.command("edit")
@click.argument("category_id", type=int)
@click.option("--name")
@click.option("--sort-order", type=int)
@click.pass_context
def categories_edit(ctx, category_id, name, sort_order):
    """Edit a category."""
    with ctx.obj["engine"].connect() as conn:
        edit_category(conn, category_id, name=name, sort_order=sort_order)
    click.echo(f"Updated category {category_id}")


@categories.command("delete")
@click.argument("name")
@click.pass_context
def categories_delete(ctx, name):
    """Delete a category."""
    with ctx.obj["engine"].connect() as conn:
        delete_category(conn, name=name)
    click.echo(f"Deleted category: {name}")
