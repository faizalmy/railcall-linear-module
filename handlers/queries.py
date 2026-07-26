"""GraphQL queries for Linear API."""

# Issue queries
LIST_ISSUES = """
query($first: Int, $after: String, $filter: IssueFilter) {
  issues(first: $first, after: $after, filter: $filter) {
    nodes {
      id
      identifier
      title
      description
      priority
      state {
        id
        name
        color
      }
      assignee {
        id
        name
        email
      }
      team {
        id
        name
        key
      }
      project {
        id
        name
      }
      createdAt
      updatedAt
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

GET_ISSUE = """
query($id: String!) {
  issue(id: $id) {
    id
    identifier
    title
    description
    priority
    state {
      id
      name
      color
    }
    assignee {
      id
      name
      email
    }
    team {
      id
      name
      key
    }
    project {
      id
      name
    }
    labels {
      nodes {
        id
        name
        color
      }
    }
    comments {
      nodes {
        id
        body
        createdAt
        user {
          id
          name
        }
      }
    }
    createdAt
    updatedAt
  }
}
"""

CREATE_ISSUE = """
mutation($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id
      identifier
      title
      state {
        id
        name
      }
      assignee {
        id
        name
      }
      team {
        id
        name
        key
      }
    }
  }
}
"""

UPDATE_ISSUE = """
mutation($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue {
      id
      identifier
      title
      state {
        id
        name
      }
      assignee {
        id
        name
      }
    }
  }
}
"""

DELETE_ISSUE = """
mutation($id: String!) {
  issueDelete(id: $id) {
    success
  }
}
"""

# Team queries
LIST_TEAMS = """
query($first: Int, $after: String) {
  teams(first: $first, after: $after) {
    nodes {
      id
      name
      key
      description
      createdAt
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

GET_TEAM = """
query($id: String!) {
  team(id: $id) {
    id
    name
    key
    description
    states {
      nodes {
        id
        name
        color
        type
      }
    }
    members {
      nodes {
        id
        name
        email
      }
    }
    createdAt
  }
}
"""

# Project queries
LIST_PROJECTS = """
query($first: Int, $after: String) {
  projects(first: $first, after: $after) {
    nodes {
      id
      name
      description
      state
      createdAt
      updatedAt
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

GET_PROJECT = """
query($id: String!) {
  project(id: $id) {
    id
    name
    description
    state
    teams {
      nodes {
        id
        name
        key
      }
    }
    createdAt
    updatedAt
  }
}
"""

CREATE_PROJECT = """
mutation($input: ProjectCreateInput!) {
  projectCreate(input: $input) {
    success
    project {
      id
      name
      state
    }
  }
}
"""

UPDATE_PROJECT = """
mutation($id: String!, $input: ProjectUpdateInput!) {
  projectUpdate(id: $id, input: $input) {
    success
    project {
      id
      name
      state
    }
  }
}
"""

# User queries
LIST_USERS = """
query($first: Int, $after: String) {
  users(first: $first, after: $after) {
    nodes {
      id
      name
      email
      active
      createdAt
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

GET_USER = """
query($id: String!) {
  user(id: $id) {
    id
    name
    email
    active
    teams {
      nodes {
        id
        name
        key
      }
    }
    createdAt
  }
}
"""

# State queries
LIST_STATES = """
query($teamId: String, $first: Int, $after: String) {
  workflowStates(filter: { team: { id: { eq: $teamId } } }, first: $first, after: $after) {
    nodes {
      id
      name
      color
      type
      position
      team {
        id
        name
        key
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

CREATE_STATE = """
mutation($input: WorkflowStateCreateInput!) {
  workflowStateCreate(input: $input) {
    success
    workflowState {
      id
      name
      color
      type
    }
  }
}
"""

UPDATE_STATE = """
mutation($id: String!, $input: WorkflowStateUpdateInput!) {
  workflowStateUpdate(id: $id, input: $input) {
    success
    workflowState {
      id
      name
      color
      type
    }
  }
}
"""

# Label queries
LIST_LABELS = """
query($teamId: String, $first: Int, $after: String) {
  issueLabels(filter: { team: { id: { eq: $teamId } } }, first: $first, after: $after) {
    nodes {
      id
      name
      color
      description
      team {
        id
        name
        key
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

CREATE_LABEL = """
mutation($input: IssueLabelCreateInput!) {
  issueLabelCreate(input: $input) {
    success
    issueLabel {
      id
      name
      color
    }
  }
}
"""

UPDATE_LABEL = """
mutation($id: String!, $input: IssueLabelUpdateInput!) {
  issueLabelUpdate(id: $id, input: $input) {
    success
    issueLabel {
      id
      name
      color
    }
  }
}
"""

# Cycle queries
LIST_CYCLES = """
query($teamId: String!, $first: Int, $after: String) {
  cycles(filter: { team: { id: { eq: $teamId } } }, first: $first, after: $after) {
    nodes {
      id
      number
      name
      startsAt
      endsAt
      completedAt
      team {
        id
        name
        key
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

GET_CYCLE = """
query($id: String!) {
  cycle(id: $id) {
    id
    number
    name
    startsAt
    endsAt
    completedAt
    team {
      id
      name
      key
    }
    issues {
      nodes {
        id
        identifier
        title
      }
    }
  }
}
"""

CREATE_CYCLE = """
mutation($input: CycleCreateInput!) {
  cycleCreate(input: $input) {
    success
    cycle {
      id
      number
      name
      startsAt
      endsAt
    }
  }
}
"""

UPDATE_CYCLE = """
mutation($id: String!, $input: CycleUpdateInput!) {
  cycleUpdate(id: $id, input: $input) {
    success
    cycle {
      id
      number
      name
    }
  }
}
"""

# Comment queries
LIST_COMMENTS = """
query($issueId: String!, $first: Int, $after: String) {
  comments(filter: { issue: { id: { eq: $issueId } } }, first: $first, after: $after) {
    nodes {
      id
      body
      createdAt
      updatedAt
      user {
        id
        name
        email
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

CREATE_COMMENT = """
mutation($input: CommentCreateInput!) {
  commentCreate(input: $input) {
    success
    comment {
      id
      body
      createdAt
      user {
        id
        name
      }
    }
  }
}
"""

UPDATE_COMMENT = """
mutation($id: String!, $input: CommentUpdateInput!) {
  commentUpdate(id: $id, input: $input) {
    success
    comment {
      id
      body
      updatedAt
    }
  }
}
"""

DELETE_COMMENT = """
mutation($id: String!) {
  commentDelete(id: $id) {
    success
  }
}
"""

# Webhook queries
LIST_WEBHOOKS = """
query($first: Int, $after: String) {
  webhooks(first: $first, after: $after) {
    nodes {
      id
      url
      enabled
      createdAt
      updatedAt
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

CREATE_WEBHOOK = """
mutation($input: WebhookCreateInput!) {
  webhookCreate(input: $input) {
    success
    webhook {
      id
      url
      enabled
    }
  }
}
"""

UPDATE_WEBHOOK = """
mutation($id: String!, $input: WebhookUpdateInput!) {
  webhookUpdate(id: $id, input: $input) {
    success
    webhook {
      id
      url
      enabled
    }
  }
}
"""

DELETE_WEBHOOK = """
mutation($id: String!) {
  webhookDelete(id: $id) {
    success
  }
}
"""

# Milestone queries
LIST_MILESTONES = """
query($first: Int, $after: String) {
  milestones(first: $first, after: $after) {
    nodes {
      id
      name
      description
      targetDate
      createdAt
      updatedAt
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

CREATE_MILESTONE = """
mutation($input: MilestoneCreateInput!) {
  milestoneCreate(input: $input) {
    success
    milestone {
      id
      name
      targetDate
    }
  }
}
"""

UPDATE_MILESTONE = """
mutation($id: String!, $input: MilestoneUpdateInput!) {
  milestoneUpdate(id: $id, input: $input) {
    success
    milestone {
      id
      name
      targetDate
    }
  }
}
"""
