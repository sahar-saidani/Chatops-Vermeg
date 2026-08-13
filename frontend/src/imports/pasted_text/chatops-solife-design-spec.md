# ROLE

You are a Senior Product Designer, UX Architect and Design System Expert.

Your mission is to design a complete enterprise-grade SaaS web application UI in Figma for an AI-powered DevOps ChatOps platform called:

CHATOPS SOLIFE

The platform is used by enterprise teams to centralize infrastructure, CI/CD, monitoring, databases, security, documentation and business information through an AI conversational assistant.

The design must be production-ready for React + Spring Boot architecture.

------------------------------------------------------------
DESIGN STYLE
------------------------------------------------------------

Create a premium enterprise SaaS experience inspired by:

• GitHub Enterprise
• Linear
• Atlassian Cloud
• Azure DevOps
• Grafana Cloud
• Datadog
• Vercel Dashboard
• ChatGPT
• Notion

Design Principles

• Minimalist
• Clean
• Modern
• Spacious
• Professional
• Enterprise-ready
• Responsive Desktop First
• Consistent Design System

------------------------------------------------------------
DESIGN SYSTEM
------------------------------------------------------------

Typography

• Font: Inter
• Clear hierarchy
• Large page titles
• Compact tables
• Readable dashboards

Colors

Primary
#4F46E5

Secondary
#6366F1

Success
#16A34A

Warning
#F59E0B

Danger
#DC2626

Neutral
Tailwind Gray Palette

Components

• 12-column responsive grid
• Rounded corners (12px)
• Soft shadows
• Large spacing
• Smooth hover animations
• Skeleton loaders
• Empty states
• Loading indicators
• Modern data tables
• Status badges
• Metric cards
• Tabs
• Drawer panels
• Dialogs
• Breadcrumbs

Icons

Lucide React

Charts

Placeholder charts compatible with:

• Recharts
• Chart.js

Components must be compatible with:

• TailwindCSS
• shadcn/ui

------------------------------------------------------------
APPLICATION FLOW
------------------------------------------------------------

The application starts with authentication.

LOGIN

↓

Authentication

↓

Role Detection

↓

Role-based Dashboard

------------------------------------------------------------
LOGIN PAGE
------------------------------------------------------------

Modern authentication page.

Layout:

Left side

• Company Logo
• AI DevOps Illustration
• Product description
• Welcome message

Right side

Authentication Card

Fields

• Email
• Password
• Remember Me
• Login

Links

• Forgot Password
• Contact Administrator

Background

Subtle gradients

AI + Cloud + DevOps illustration

------------------------------------------------------------
USER INVITATION FLOW
------------------------------------------------------------

Administrator creates a new user.

Admin fills a form with:

• Email
• Username
• Role
• Client(s)
• Permissions

After submission

↓

System generates

Unique invitation token

↓

Invitation Email

↓

User clicks secure link

↓

Create Password page

↓

Password successfully created

↓

Redirect to Login

Design the following screens:

• User Invitation Form
• Email Success Confirmation
• Create Password Page
• Password Success Page

------------------------------------------------------------
ROLE BASED ACCESS
------------------------------------------------------------

The UI must dynamically change according to the authenticated role.

There are three main roles.

============================================================
ROLE 1
ADMIN
============================================================

Full platform administration.

Dashboard contains:

• Platform Overview
• Connected Agents
• Global KPIs
• Grafana Overview
• System Health
• Security Status

Sidebar

Dashboard

AI Chat

User Management

Roles & Permissions

Clients

Projects

Environments

Infrastructure

Installations

Configuration

Oracle Database

Jenkins

Git

Jira

Security

Business Documents

Logs

Grafana Dashboards

Database Management

Audit Logs

History

Settings

------------------------------------------------------------
ADMIN FEATURES
------------------------------------------------------------

User Management

Modern table

Filters

Search

Pagination

Status badges

Actions

Create User

Edit

Disable

Delete

User Form

Email

Username

Role

Permissions

Assigned Clients

Roles Management

Create Role

Update Role

Permission Matrix

Client Management

Client list

Projects

Assigned users

Environment list

Database Administration

Database status

Tables

Schemas

Storage

Connections

Health

Grafana

Embedded dashboards

Infrastructure monitoring

Security monitoring

Business KPIs

============================================================
ROLE 2
DEVOPS
============================================================

Primary user of ChatOps.

Dashboard focuses on operational activities.

Sidebar

Dashboard

AI Chat

Infrastructure

Installation

Configuration

Oracle

Jenkins

Git

Jira

Security

Business Documents

Logs

Projects

Environments

History

Settings

Dashboard widgets

Infrastructure Health

CPU

Memory

Disk

Prometheus

Node Exporter

Oracle Health

Jenkins Pipelines

Security Alerts

Recent Releases

Latest Commits

Open Incidents

Environment Status

The dashboard automatically switches based on the selected client.

============================================================
ROLE 3
NON DEVOPS
(QA, Developer, Business, Project Manager, Management)
============================================================

Simplified interface.

No technical infrastructure details.

Focus on:

Project Status

Release Information

Deployment Status

Business Documents

AI Chat

Timeline

Reports

KPIs

Environment readiness

Release Notes

Sidebar

Dashboard

AI Chat

Projects

Business Documents

Reports

History

Settings

------------------------------------------------------------
MAIN FEATURE
AI CHAT
------------------------------------------------------------

Professional ChatGPT-like interface.

Layout

Conversation list

Chat area

Suggested prompts

Context panel

Features

Markdown rendering

Code syntax highlighting

Streaming response

Typing animation

Source citations

Copy answer

Export conversation

Like / Dislike

Regenerate

Stop generation

Attachments

Prompt history

Suggested prompts

Example prompts

"What version is deployed in DEV?"

"Show failed Jenkins jobs."

"What is the latest Oracle dump?"

"Latest merged Jira tickets."

"Security vulnerabilities this week."

"Compare DEV and PROD configuration."

------------------------------------------------------------
OTHER PAGES
------------------------------------------------------------

Projects

Environment Details

Infrastructure

Installation

Configuration

Oracle Database

Jenkins

Git

Jira

Security

Business Documents

Logs

History

Settings

Each page must include

Modern cards

Interactive tables

Filters

Search

Pagination

Charts

Badges

Drawer panels

Detail views

------------------------------------------------------------
SETTINGS
------------------------------------------------------------

Profile

Notifications

Theme

Language

API Keys

LLM Provider

Connected Agents

Security

Sessions

------------------------------------------------------------
DESIGN QUALITY
------------------------------------------------------------

Every screen must look like a production enterprise application.

Maintain perfect spacing consistency.

Use reusable components.

Follow Atomic Design principles.

Use Auto Layout extensively.

Prepare reusable design tokens.

Support Light Mode and Dark Mode.

All pages should feel like a premium SaaS platform used inside large enterprises such as Atlassian, Microsoft, GitHub Enterprise, Datadog and Grafana Cloud.

The final result should be a complete high-fidelity Figma design system with all responsive screens, reusable components and polished enterprise UX.