"""Jenkins API endpoint helpers."""

from __future__ import annotations


class JenkinsAPI:
    """Utility class that builds Jenkins API endpoints."""

    INFO = "/api/json"
    JOBS = "/api/json?tree=jobs[name,url,color,description,lastBuild[number,url],lastSuccessfulBuild[number,url],lastFailedBuild[number,url],buildable]"

    @staticmethod
    def job(job_name: str) -> str:
        return f"/job/{job_name}/api/json"

    @staticmethod
    def builds(job_name: str) -> str:
        return (
            f"/job/{job_name}/api/json?tree="
            "builds[number,url,result,duration,timestamp,building,"
            "actions[causes[userId,userName,shortDescription],"
            "lastBuiltRevision[SHA1,branch[name]],"
            "buildsByBranchName,*],"
            "changeSets[items[commitId,msg,author[fullName],timestamp]]]"
        )

    @staticmethod
    def build(job_name: str, build_number: int) -> str:
        return (
            f"/job/{job_name}/{build_number}/api/json?tree="
            "number,url,result,duration,timestamp,building,"
            "actions[causes[userId,userName,shortDescription],"
            "lastBuiltRevision[SHA1,branch[name]],"
            "buildsByBranchName,*],"
            "changeSets[items[commitId,msg,author[fullName],timestamp]],"
            "stages[name,status,durationMillis,error{message}]"
        )

    @staticmethod
    def console(job_name: str, build_number: int) -> str:
        return f"/job/{job_name}/{build_number}/consoleText"

    @staticmethod
    def wfapi(job_name: str, build_number: int) -> str:
        return f"/job/{job_name}/{build_number}/wfapi/describe"
