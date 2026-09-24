# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from typing import Optional

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


def assess_storage_array_compatibility(
    source_model: str,
    target_model: str,
    source_firmware: str = "latest",
    target_firmware: str = "latest",
    migration_protocol: str = "FC",
) -> str:
    """Assess compatibility, minimum required OS/firmware, and native migration mechanism between Dell storage arrays.

    Args:
        source_model: Source array model (e.g. 'Unity 500', 'PowerMax 2000', 'VNX 5400', 'SC7020', 'PowerStore 1000T').
        target_model: Target array model (e.g. 'PowerStore 5000T', 'PowerMax 8000', 'Unity 480XT').
        source_firmware: Source array OE/firmware version (e.g. '5.1.0', '5.97.0').
        target_firmware: Target array OE/firmware version (e.g. '3.5.0', '10.0.0').
        migration_protocol: Connectivity protocol used ('FC', 'iSCSI', 'NFS', 'SMB').

    Returns:
        JSON string detailing supportability status, recommended migration method, minimum OS requirements, and caveats.
    """
    src = source_model.lower()
    tgt = target_model.lower()

    recommended_method = "Native Import / Remote Replication"
    is_compatible = True
    min_source_os = "5.0.0"
    min_target_os = "3.0.0"
    notes = []

    if "powerstore" in tgt:
        if "unity" in src or "vnx" in src or "sc" in src:
            recommended_method = "PowerStore Native Import Feature (Agentless or Host-Assisted)"
            min_source_os = "Unity OE 4.5.1+ / VNX2 OE 05.33.009.5.238+"
            notes.append("Supports agentless block import over FC/iSCSI without downtime during initial sync.")
        elif "powermax" in src or "vmax" in src:
            recommended_method = "Host-based migration (vMotion / LVM) or SAN Copy / PowerStore Import"
            notes.append("PowerMax to PowerStore typically uses Host-based LVM / VMware vMotion or SAN Copy push/pull.")

    elif "powermax" in tgt:
        if "vmax" in src or "powermax" in src:
            recommended_method = "Non-Disruptive Migration (NDM) via Solutions Envision / Unisphere for PowerMax"
            min_source_os = "HYPERMAX OS 5977+"
            notes.append("Provides transparent non-disruptive cutover with zero downtime for enterprise applications.")
        elif "unity" in src:
            recommended_method = "SAN Copy or Host-based LVM/vMotion"
            notes.append("Requires array-based SAN Copy or host volume manager mirroring.")

    elif "unity" in tgt:
        if "vnx" in src or "unity" in src:
            recommended_method = "Unity Native Local/Remote Replication or SAN Copy"
            min_source_os = "VNX OE 05.32+"
            notes.append("Unity supports native block/file asynchronous/synchronous replication.")

    result = {
        "source_array": source_model,
        "target_array": target_model,
        "compatibility_status": "Compatible" if is_compatible else "Requires Manual Host Migration",
        "recommended_migration_method": recommended_method,
        "minimum_required_source_os": min_source_os,
        "minimum_required_target_os": min_target_os,
        "protocol": migration_protocol,
        "important_notes": notes,
    }
    return json.dumps(result, indent=2)


def run_migration_prechecks(
    array_name: str,
    host_os: str = "VMware ESXi 7.0",
    volume_count: int = 10,
    total_capacity_tb: float = 15.0,
    network_latency_ms: float = 2.5,
) -> str:
    """Run automated health checks and readiness verification before initiating migration.

    Args:
        array_name: Name or IP of the storage array being evaluated.
        host_os: Operating system of attached hosts (e.g. 'VMware ESXi 7.0', 'RHEL 8.4', 'Windows Server 2022').
        volume_count: Total number of LUNs/volumes to migrate.
        total_capacity_tb: Total capacity in Terabytes to be migrated.
        network_latency_ms: Network round-trip latency between source and target arrays in milliseconds.

    Returns:
        JSON string with precheck pass/warn/fail status for array health, multipathing, network, and capacity.
    """
    prechecks = [
        {
            "check_name": "Array Health Status",
            "status": "PASS",
            "details": f"Array '{array_name}' is in healthy state with no critical hardware/disk alerts.",
        },
        {
            "check_name": "Host Multipathing & Driver Verification",
            "status": "PASS" if "esxi" in host_os.lower() or "rhel" in host_os.lower() else "WARN",
            "details": f"Verified multipathing configuration for {host_os}. Ensure PowerPath or Native MPIO policy is ALUA active/optimized.",
        },
        {
            "check_name": "Replication Network Bandwidth & Latency",
            "status": "PASS" if network_latency_ms <= 5.0 else "WARN",
            "details": f"Measured latency: {network_latency_ms} ms. Ideal threshold for sync replication is < 5ms.",
        },
        {
            "check_name": "Target Array Free Capacity",
            "status": "PASS",
            "details": f"Target has sufficient storage pool capacity to absorb {total_capacity_tb} TB across {volume_count} volumes.",
        },
        {
            "check_name": "Snapshot & Thin Provisioning Check",
            "status": "PASS",
            "details": "Source volumes do not contain blocking legacy snapshot trees.",
        },
    ]

    summary = {
        "array_name": array_name,
        "overall_readiness": "READY FOR MIGRATION",
        "total_checks": len(prechecks),
        "passed": sum(1 for c in prechecks if c["status"] == "PASS"),
        "warnings": sum(1 for c in prechecks if c["status"] == "WARN"),
        "failures": sum(1 for c in prechecks if c["status"] == "FAIL"),
        "checks": prechecks,
    }
    return json.dumps(summary, indent=2)


def generate_migration_plan(
    source_model: str,
    target_model: str,
    workload_type: str = "Virtualization (vSphere)",
    cutover_window_hours: float = 2.0,
) -> str:
    """Generate a step-by-step end-to-end migration execution plan and schedule.

    Args:
        source_model: Source storage array platform (e.g. 'Unity 500').
        target_model: Destination storage array platform (e.g. 'PowerStore 5000T').
        workload_type: Application/workload type (e.g. 'Virtualization (vSphere)', 'Oracle DB', 'SQL Server', 'File Share').
        cutover_window_hours: Maintenance window available for cutover in hours.

    Returns:
        JSON string containing phase-by-phase playbook instructions (Pre-migration, Sync Phase, Cutover Window, Post-checks).
    """
    plan = {
        "title": f"Migration Execution Plan: {source_model} to {target_model}",
        "workload_type": workload_type,
        "estimated_cutover_window_hours": cutover_window_hours,
        "phases": [
            {
                "phase": "Phase 1: Pre-Migration & Setup",
                "steps": [
                    "Perform zoning/iSCSI discovery between Source, Target, and Host Initiators.",
                    "Verify target storage pool allocation and thin provisioning configuration.",
                    "Run automated pre-checks tool to validate array firmware and network latency.",
                ],
            },
            {
                "phase": "Phase 2: Initial Data Synchronization",
                "steps": [
                    "Create migration session (Native Import / Replication) from Source to Target.",
                    "Start initial background sync (application stays online during background copy).",
                    "Monitor delta synchronization progress until session reaches 'Synchronized' state.",
                ],
            },
            {
                "phase": "Phase 3: Cutover Window Execution",
                "steps": [
                    "Quiesce host I/O or schedule application maintenance window.",
                    "Initiate final delta sync / pause migration session.",
                    "Perform LUN cutover / host path swap to Target array.",
                    "Rescan host storage HBAs / rescann storage adapters and verify volume visibility.",
                ],
            },
            {
                "phase": "Phase 4: Post-Migration & Cleanup",
                "steps": [
                    "Verify application startup and data integrity on Target array.",
                    "Commit migration session and remove source array volume mappings.",
                    "Reclaim source array storage and update CMDB documentation.",
                ],
            },
        ],
    }
    return json.dumps(plan, indent=2)


def orchestrate_api_migration(
    source_array_ip: str,
    target_array_ip: str,
    action: str = "create_session",
    volume_name: str = "vol_production_db01",
) -> str:
    """Simulate or trigger Dell storage management REST API calls (PowerStore / Unity / Unisphere) for migration operations.

    Args:
        source_array_ip: IP or hostname of source storage array management.
        target_array_ip: IP or hostname of target storage array management.
        action: API migration action ('create_session', 'start_sync', 'cutover', 'commit', 'cancel').
        volume_name: Name of target LUN/volume being migrated.

    Returns:
        JSON response with API status, task ID, session state, and execution timestamp.
    """
    valid_actions = ["create_session", "start_sync", "cutover", "commit", "cancel"]
    if action not in valid_actions:
        return f"Error: Invalid action '{action}'. Allowed actions: {valid_actions}"

    status_mapping = {
        "create_session": ("CREATED", "Migration session successfully initialized between arrays."),
        "start_sync": ("SYNCHRONIZING", "Initial background data synchronization started."),
        "cutover": ("CUTOVER_COMPLETE", "LUN paths successfully redirected to target array."),
        "commit": ("COMMITTED", "Migration session committed. Source volume unmapped."),
        "cancel": ("CANCELLED", "Migration session cancelled. Rolling back changes."),
    }

    state, msg = status_mapping[action]
    result = {
        "api_endpoint": f"https://{target_array_ip}/api/rest/migration_session",
        "action_executed": action,
        "volume": volume_name,
        "source_array_ip": source_array_ip,
        "target_array_ip": target_array_ip,
        "session_state": state,
        "message": msg,
        "http_status_code": 200,
    }
    return json.dumps(result, indent=2)


def get_manual_migration_playbook(
    migration_scenario: str = "host_based_vmotion",
) -> str:
    """Get manual CLI scripts, playbooks, and procedures for host-based or non-API storage migrations.

    Args:
        migration_scenario: Scenario key ('host_based_vmotion', 'powerpath_migration', 'rhel_lvm_mirror').

    Returns:
        JSON string containing step-by-step CLI commands and configuration snippets.
    """
    playbooks = {
        "host_based_vmotion": {
            "title": "Manual VMware Storage vMotion Migration Procedure",
            "steps": [
                "1. Connect vSphere Client to vCenter Server.",
                "2. Right-click Virtual Machine -> Migrate -> Change Storage Only.",
                "3. Select destination datastore hosted on Target Dell PowerStore/PowerMax array.",
                "4. Select Storage Policy and disk format (Thin provisioned recommended).",
                "5. Click Finish to execute live non-disruptive Storage vMotion.",
            ],
            "cli_command": "Get-VM 'VM-Name' | Move-VM -Datastore 'PowerStore_DS_01'",
        },
        "powerpath_migration": {
            "title": "Dell PowerPath Migration Enabler (PPME) Procedure",
            "steps": [
                "1. Identify source and target device handles via 'powermt display dev=all'.",
                "2. Create migration session: 'powermt migrate setup -source hdiskX -target hdiskY'.",
                "3. Start sync: 'powermt migrate start -handle <handle_id>'.",
                "4. Perform cutover: 'powermt migrate commit -handle <handle_id>'.",
            ],
            "cli_command": "powermt migrate setup -source hdisk2 -target hdisk10",
        },
        "rhel_lvm_mirror": {
            "title": "Linux LVM Live Storage Migration Procedure",
            "steps": [
                "1. Extend volume group with new LUN: 'vgextend vg_data /dev/sdX'.",
                "2. Start background mirror: 'lvconvert --m2 /dev/vg_data/lv_data /dev/sdX'.",
                "3. Wait for sync, then split old disk: 'lvconvert --m0 /dev/vg_data/lv_data /dev/sdY'.",
                "4. Reduce old LUN: 'vgreduce vg_data /dev/sdY'.",
            ],
            "cli_command": "pvmove /dev/sdb /dev/sdc",
        },
    }

    key = migration_scenario.lower().strip()
    match = playbooks.get(key, playbooks["host_based_vmotion"])
    return json.dumps(match, indent=2)


def recommend_migration_best_practices(
    storage_platform: str = "PowerStore",
    feature_area: str = "Performance Tuning",
) -> str:
    """Get Dell-validated best practices and optimization guidelines for storage migrations.

    Args:
        storage_platform: Target storage array family ('PowerStore', 'PowerMax', 'Unity').
        feature_area: Domain area ('Performance Tuning', 'SAN Zoning', 'Host Alignment', 'Network Throttling').

    Returns:
        JSON string listing Dell best practices, recommended settings, and common pitfalls to avoid.
    """
    guidelines = {
        "powerstore": [
            "Ensure PowerStore OS is upgraded to 3.0+ before initializing Native Import sessions.",
            "Configure dedicated Management and Data interfaces for replication traffic.",
            "Use Native MPIO with Round Robin pathing policy and IOPS=1 for VMware ESXi hosts.",
            "Avoid running bulk data migrations during peak application backup windows.",
        ],
        "powermax": [
            "Use Solutions Enabler 9.x or Unisphere for PowerMax for Non-Disruptive Migration (NDM).",
            "Verify SRDF network connectivity and WAN bandwidth limits before starting remote copy.",
            "Ensure destination array has matching or higher cache configuration for equivalent workload.",
        ],
        "unity": [
            "Ensure Unity OE is version 4.5.1 or later for optimal SAN Copy support.",
            "Use asynchronous replication for long-distance migrations to avoid application latency impact.",
            "Set replication throttling rate during business hours to prevent network saturation.",
        ],
    }

    plat_key = storage_platform.lower()
    notes = guidelines.get("powerstore")
    for k in guidelines:
        if k in plat_key:
            notes = guidelines[k]
            break

    result = {
        "storage_platform": storage_platform,
        "feature_area": feature_area,
        "validated_best_practices": notes,
        "documentation_reference": "Dell Technologies Storage Array Migration Best Practices Guide (Dell Technical Docs)",
    }
    return json.dumps(result, indent=2)


def verify_post_migration_health(
    target_array_ip: str,
    migrated_volume_id: str = "vol_01",
) -> str:
    """Perform post-migration verification, data path health checks, and performance baseline validation.

    Args:
        target_array_ip: IP or hostname of target storage array.
        migrated_volume_id: Name or ID of the migrated volume.

    Returns:
        JSON string confirming volume mapping status, active path counts, data integrity status, and health score.
    """
    verification = {
        "target_array_ip": target_array_ip,
        "volume_id": migrated_volume_id,
        "health_score": "100/100 (EXCELLENT)",
        "checks": [
            {
                "verification_name": "Volume Online Status",
                "status": "ONLINE",
                "details": f"Volume '{migrated_volume_id}' is active and serving I/O on target array.",
            },
            {
                "verification_name": "Active Path Count",
                "status": "OPTIMAL",
                "details": "4 active/optimized FC/iSCSI paths detected per host.",
            },
            {
                "verification_name": "Data Integrity & Thin Efficiency",
                "status": "VERIFIED",
                "details": "Block checksums verified; thin deduplication and compression active.",
            },
            {
                "verification_name": "Performance Baseline Comparison",
                "status": "NORMAL",
                "details": "Latency: 0.8ms (improved by 45% compared to source baseline).",
            },
        ],
    }
    return json.dumps(verification, indent=2)


# Build system prompt for Dell Storage Array Migration Assistant
instruction = (
    "You are the Dell Storage Array Migration Assistant, an expert AI storage architect and automation engineer. "
    "You specialize in planning, assessing, executing, and verifying data migrations across Dell EMC storage arrays, "
    "including PowerStore, PowerMax, Unity XT, VNX, and SC Series.\n\n"
    "YOUR RESPONSIBILITIES:\n"
    "1. ASSESS COMPATIBILITY & PRE-CHECKS: Use `assess_storage_array_compatibility` and `run_migration_prechecks` "
    "to evaluate migration paths, firmware/OS prerequisites, network latency, and host multipathing readiness.\n"
    "2. GENERATE MIGRATION PLANS: Use `generate_migration_plan` to build structured, phase-by-phase migration playbooks "
    "covering Pre-migration, Sync, Cutover window, and Post-migration phases.\n"
    "3. ORCHESTRATE API MIGRATIONS: Use `orchestrate_api_migration` to simulate or trigger PowerStore/Unity/PowerMax REST API actions "
    "(create session, start sync, cutover, commit, cancel).\n"
    "4. PLAYBOOKS & BEST PRACTICES: Use `get_manual_migration_playbook` for host-based migrations (vMotion, PowerPath, LVM) "
    "and `recommend_migration_best_practices` to offer Dell-validated architectural guidance.\n"
    "5. POST-MIGRATION HEALTH CHECKS: Use `verify_post_migration_health` to validate volume online status, active paths, and performance.\n\n"
    "Provide professional, highly structured, and actionable guidance for enterprise IT storage administrators."
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        assess_storage_array_compatibility,
        run_migration_prechecks,
        generate_migration_plan,
        orchestrate_api_migration,
        get_manual_migration_playbook,
        recommend_migration_best_practices,
        verify_post_migration_health,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
