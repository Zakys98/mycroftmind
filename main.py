import requests
import psycopg2
from datetime import datetime

# použít env variables
GITLAB_URL = "https://gitlab.com/api/v4"
GITLAB_TOKEN = "token"

PG_CONN = {
    "dbname": "mycroftmind",
    "user": "mycroftmind",
    "password": "mycroftmind",
    "host": "localhost",
    "port": 5432,
}


def create_tables(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        # Možná by se hodila ještě tabulka commit
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS team (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS project (
                id SERIAL PRIMARY KEY,
                name TEXT,
                team_id INT REFERENCES team(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS deployment (
                id BIGSERIAL PRIMARY KEY,
                # add deployment ID from GitLab
                environment TEXT,
                status TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                project_id INT REFERENCES project(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS incident (
                id SERIAL PRIMARY KEY,
                project_id INT REFERENCES project(id),
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP NULL
            )
            """
        )

    conn.close()


def get_all_projects() -> dict:
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    url = f"{GITLAB_URL}/projects?simple=true"
    params = {"membership": True, "per_page": 100}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def get_project_id(name: str, projects: dict) -> int:
    name = name.strip().lower()
    for project in projects:
        project_name = project.get("name", "").strip().lower()
        if project_name == name:
            return project["id"]
    return -1


def get_since_until_dates() -> tuple:
    yesterday = datetime.now().date().replace(day=datetime.now().day - 1)
    since = datetime.combine(yesterday, datetime.min.time()).isoformat() + "Z"
    until = datetime.combine(yesterday, datetime.max.time()).isoformat() + "Z"
    return since, until


def get_deployments(project_id: int) -> dict:
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    since, until = get_since_until_dates()

    url = f"{GITLAB_URL}/projects/{project_id}/deployments"
    params = {"updated_after": since, "updated_before": until}

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def save_deployments(
    conn: psycopg2.extensions.connection, project_id: int, deployments: dict
) -> None:
    with conn.cursor() as cur:
        for deployment in deployments:
            cur.execute(
                """
                INSERT INTO deployment (environment, status, created_at, updated_at, project_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """,
                (
                    deployment["environment"]["name"] if deployment.get("environment") else "test",
                    deployment["status"],
                    deployment["created_at"],
                    deployment["updated_at"],
                    project_id,
                ),
            )


def get_issues(project_id: int) -> dict:
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    since, until = get_since_until_dates()

    url = f"{GITLAB_URL}/projects/{project_id}/issues"
    params = {"issue_type": "incident", "created_after": since, "created_before": until}

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def save_issues(conn: psycopg2.extensions.connection, project_id: int, issues: dict) -> None:
    with conn.cursor() as cur:
        for issue in issues:
            cur.execute(
                """
                INSERT INTO incident (project_id, title, created_at, closed_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """,
                (
                    project_id,
                    issue["title"],
                    issue["created_at"],
                    issue["closed_at"],
                ),
            )


def main() -> None:
    conn = psycopg2.connect(**PG_CONN)
    conn.autocommit = True

    create_tables(conn)
    projects = get_all_projects()

    with open("input_file.txt") as file:
        names = file.readlines()

    for name in names:
        project_id = get_project_id(name, projects)
        if project_id == -1:
            print(f"Project '{name.strip()}' not found.")
            continue

        deployments = get_deployments(project_id)
        if deployments:
            save_deployments(conn, project_id, deployments)

        issues = get_issues(project_id)
        if issues:
            save_issues(conn, project_id, issues)

    conn.close()


if __name__ == "__main__":
    main()
