import os
import json
import random
import discord
from discord.ext import commands
from difflib import get_close_matches
from datetime import datetime

JANUS_ACTIVE = False

# IDs for DM control and crew-facing terminal
ROOT_COMMAND_CHANNEL_ID = 1350826672504700938# replace with your #root-command channel ID
CREW_TERMINAL_CHANNEL_ID = 1350922295782281297# IDs for DM control and crew-facing terminal

# --- File and Directory Setup ---
base_dir = os.path.dirname(os.path.abspath(__file__))
zone_state_path = os.path.join(base_dir, "zone_state.json")
maintenance_log_path = os.path.join(base_dir, "maintenance_log.json")
directives_path = os.path.join(base_dir, "erebus_directives.json")
with open(directives_path, "r", encoding="utf-8") as f:
    erebus_directives = json.load(f)


try:
    with open(maintenance_log_path, "r") as f:
        maintenance_log = json.load(f).get("log", [])
except FileNotFoundError:
    maintenance_log = []
try:
    with open(maintenance_log_path, "r") as f:
        maintenance_log = json.load(f).get("log", [])
except FileNotFoundError:
    maintenance_log = []

# --- Data Loading ---
with open(os.path.join(base_dir, "ship_data.json"), "r") as file:
    ship_profile = json.load(file)

try:
    with open(zone_state_path, "r") as f:
        zone_states = json.load(f)
except FileNotFoundError:
    zone_states = {}

# --- Helper Functions ---
def log_maintenance(action, zone):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    maintenance_log.append(f"{timestamp} — {zone}: {action}")
    with open(maintenance_log_path, "w") as f:
        json.dump({"log": maintenance_log}, f, indent=4)

def save_zone_states():
    """Save the current zone states to the JSON file."""
    with open(zone_state_path, "w") as f:
        json.dump(zone_states, f, indent=4)

# Zone name resolution system
zone_aliases = {
    "bridge": "Command Bridge",
    "command": "Command Bridge",

    "cryo": "Crew Quarters & Cryostasis Wing",
    "quarters": "Crew Quarters & Cryostasis Wing",
    "crew": "Crew Quarters & Cryostasis Wing",

    "med": "Medical Bay",
    "medbay": "Medical Bay",
    "medical": "Medical Bay",

    "reactor": "Reactor Room",
    "reactor room": "Reactor Room",
    "engineering": "Reactor Room",

    "extractor": "Extractor Control Station",
    "extractors": "Extractor Control Station",
    "control": "Extractor Control Station",

    "cargo": "Cargo Hold",
    "hold": "Cargo Hold",

    "maintenance": "Maintenance Access & System Shafts",
    "shafts": "Maintenance Access & System Shafts",
    "vents": "Maintenance Access & System Shafts"
}

ZONE_CONNECTIONS = {
    "Command Bridge": ["Crew Quarters & Cryostasis Wing"],
    "Crew Quarters & Cryostasis Wing": ["Command Bridge", "Medical Bay", "Maintenance Access & System Shafts"],
    "Medical Bay": ["Crew Quarters & Cryostasis Wing"],
    "Maintenance Access & System Shafts": ["Crew Quarters & Cryostasis Wing", "Reactor Room"],
    "Reactor Room": ["Maintenance Access & System Shafts", "Extractor Control Station", "Cargo Hold"],
    "Extractor Control Station": ["Reactor Room"],
    "Cargo Hold": ["Reactor Room"]
} 
def resolve_zone(name):
    """Resolve zone name from input to full zone name."""
    lowered = name.lower().strip()
    if lowered in zone_aliases:
        return zone_aliases[lowered]
    match = get_close_matches(lowered, [z.lower() for z in zone_states], n=1, cutoff=0.4)
    if match:
        return next(z for z in zone_states if z.lower() == match[0])
    return None

def format_directive(directive):
    """Format an Erebus Directive into a full corporate JANUS message."""
    import random
    # Generate a directive ID like EX-442-B
    id_number = random.randint(100, 999)
    id_suffix = random.choice(["A", "B", "C", "D", "E"])
    directive_id = f"EX-{id_number}-{id_suffix}"

    return (
        f"JANUS: New Erebus Directive Issued.\n\n"
        f"Directive ID: {directive_id}\n"
        f"Title: {directive['title']}\n"
        f"Location: {directive['location']}\n"
        f"Summary: {directive['summary']}\n"
        f"Priority Level: {directive['priority']}\n"
        f"Compliance Note: {directive['compliance']}"
    )

# --- Main Bot Setup ---
# This function needs to be called directly for the commands to register properly
def setup(bot):
    # --- Ship Information Commands ---
    @bot.command(name="janus_on")
    async def janus_on(ctx):
        global JANUS_ACTIVE
        JANUS_ACTIVE = True
        await ctx.send("JANUS: Systems online. Operational control resumed.")

    @bot.command(name="janus_off")
    async def janus_off(ctx):
        global JANUS_ACTIVE
        JANUS_ACTIVE = False
        await ctx.send("JANUS: Systems entering standby mode.")
    
    @bot.command(name="ship")
    async def ship_command(ctx, *, topic=None):
        if topic is None:
            name = ship_profile["ship_name"]
            owner = ship_profile["owner"]
            crew_max = ship_profile["crew"]["maximum_complement"]
            extractors = ship_profile["extraction_systems"]["extractor_units"]
            ai_name = ship_profile["ai_name"]
            commissioned = ship_profile["commissioned_year"]

            embed = discord.Embed(
                title=f"Vessel Overview — {name}",
                description=f"{name} is an {ship_profile['class']}, commissioned in {commissioned} at the {ship_profile['manufactured_at']}.",
                color=discord.Color.dark_blue()
            )
            embed.add_field(name="Owner", value=owner, inline=True)
            embed.add_field(name="AI System", value=ai_name, inline=True)
            embed.add_field(name="Crew Capacity", value=f"{crew_max} personnel", inline=True)
            embed.add_field(name="Extractor Units", value=f"{extractors}", inline=True)
            embed.set_footer(text=f"{name} — Erebus Corp Resource Harvester")
            await ctx.send(embed=embed)
            return

        # Display information about a specific room/zone (exact match)
        topic = topic.lower().strip()

        for zone in ship_profile["ship_zones"]:
            if topic == zone["zone_name"].lower():
                embed = discord.Embed(
                    title=zone["zone_name"],
                    description=zone["description"],
                    color=discord.Color.orange()
                )
                embed.set_footer(text=f"{ship_profile['ship_name']} — Erebus Corp Resource Harvester")
                await ctx.send(embed=embed)
                return

        await ctx.send("No match found. Try `!ship reactor room`, `!ship medical bay`, or `!help_ship`.")

    @bot.command(name="deckplan")
    async def deckplan_command(ctx):
        deckplan_data = ship_profile.get("deckplan", {})
        if not deckplan_data:
            await ctx.send("JANUS: Deckplan data not available in ship registry.")
            return
            
        embed = discord.Embed(
            title="Persephone Deckplan",
            description="Internal structure by deck — Erebus Corp proprietary configuration.",
            color=discord.Color.dark_blue()
        )
        
        for deck, zones in deckplan_data.items():
            embed.add_field(name=deck, value="\n".join(zones), inline=False)
            
        embed.set_footer(text="JANUS Deckplan Interface — Erebus Systems Division")
        await ctx.send(embed=embed)
    
    @bot.command(name="rooms")
    async def rooms_command(ctx):
        zone_names = [zone["zone_name"] for zone in ship_profile["ship_zones"]]
        embed = discord.Embed(
            title="Persephone Zone Directory",
            description="All operational ship zones currently mapped.",
            color=discord.Color.dark_blue()
        )
        
        for zone in zone_names:
            embed.add_field(name="•", value=zone, inline=False)
            
        embed.set_footer(text="Mapping retrieved from Janus Core — Erebus Corp Property")
        await ctx.send(embed=embed)

    # --- Zone Status Commands ---
    @bot.command(name="status")
    async def status_command(ctx):
        embed = discord.Embed(
            title="Ship Systems Status Report",
            description="Current operational state of all monitored ship zones.",
            color=discord.Color.red()
        )
        
        for zone, state in zone_states.items():
            emoji = "✅" if state == "Online" else ("⛔" if state == "Lockdown" else "⚠️")
            embed.add_field(name=zone, value=f"{emoji} {state}", inline=False)
            
        embed.set_footer(text="Erebus Corp — Maintenance Log Certified")
        await ctx.send(embed=embed)

    @bot.command(name="report")
    async def report_command(ctx):
        damaged = [z for z, state in zone_states.items() if state == "Damaged"]
        locked = [z for z, state in zone_states.items() if state == "Lockdown"]
        total_zones = len(zone_states)
        
        embed = discord.Embed(
            title="JANUS — Mission Readiness Report",
            description=f"Analyzing {total_zones} zones for operational threats...",
            color=discord.Color.dark_teal()
        )
        
        if damaged:
            embed.add_field(name="⚠️ Damaged Zones", value="\n".join(damaged), inline=False)
        else:
            embed.add_field(name="✅ No Damage", value="All zones structurally sound.", inline=False)
            
        if locked:
            embed.add_field(name="⛔ Zones in Lockdown", value="\n".join(locked), inline=False)
        else:
            embed.add_field(name="✅ No Lockdowns", value="All zones accessible.", inline=False)
            
        embed.set_footer(text="Report generated by JANUS | Erebus Corp Oversight Module")
        await ctx.send(embed=embed)
    @bot.command(name="log")
    async def log_command(ctx):
        if not maintenance_log:
            await ctx.send("JANUS: No maintenance activity recorded.")
            return

        recent = maintenance_log[-3:]
        message = "JANUS: Recent maintenance activity:\n" + "\n".join(recent)
        await ctx.send(message)

    # --- Zone Control Commands ---
    @bot.command(name="damage")
    async def damage_command(ctx, *, zone=None):
        if not zone:
            await ctx.send("Specify a zone to mark as damaged. Example: `!damage medbay`")
            return
        real_zone = resolve_zone(zone)
        if real_zone:
            zone_states[real_zone] = "Damaged"
            save_zone_states()
            log_maintenance("Damaged", real_zone)
            await ctx.send(f"JANUS: {real_zone} reports damage to primary systems. Maintenance team required.")
        else:
            await ctx.send("JANUS: Zone not recognized. Try `!status`, `!ship`, or `!help_ship`.")

    @bot.command(name="repair")
    async def repair_command(ctx, *, zone=None):
        
        if not zone:
            await ctx.send("Specify a zone to repair. Example: `!repair medbay`")
            return
        if real_zone:
            zone_states[real_zone] = "Online"
            save_zone_states()
            log_maintenance("repaired", real_zone)
            real_zone = resolve_zone(zone)
            await ctx.send(f"JANUS: {real_zone} restored to operational status.")
        else:
            await ctx.send("JANUS: Zone not recognized. Try `!status`, `!ship`, or `!help_ship`.")

    @bot.command(name="lockdown")
    async def lockdown_command(ctx, *, zone=None):
        
        if not zone:
            await ctx.send("Specify a zone to lockdown. Example: `!lockdown medbay`")
            return
            
        real_zone = resolve_zone(zone)
        if real_zone:
            zone_states[real_zone] = "Lockdown"
            save_zone_states()
            log_maintenance("lockdown", real_zone)
            await ctx.send(f"JANUS: {real_zone} placed under isolation protocol. Crew access restricted.")
        else:
            await ctx.send("JANUS: Zone not recognized. Try `!status`, `!ship`, or `!help_ship`.")

    @bot.command(name="unlock")
    async def unlock_command(ctx, *, zone=None):
        
        if not zone:
            await ctx.send("Specify a zone to unlock. Example: `!unlock medbay`")
            return
            
        real_zone = resolve_zone(zone)
        if real_zone:
            zone_states[real_zone] = "Online"
            save_zone_states()
            log_maintenance("unlocked", real_zone)
            await ctx.send(f"JANUS: Lockdown lifted for {real_zone}. Zone access restored.")
        else:
            await ctx.send("JANUS: Zone not recognized. Try `!status`, `!ship`, or `!help_ship`.")

    @bot.command(name="reset_all")
    async def reset_all_command(ctx):
        for zone in zone_states:
            zone_states[zone] = "Online"
            save_zone_states()
            log_maintenance("reset_all", zone)
        await ctx.send("JANUS: All ship zones restored to nominal status. Maintenance backlog cleared.")

    @bot.command(name="impact")
    async def impact_command(ctx, *, cause="UNKNOWN"):
        available = list(zone_states.keys())
        
        if not available:
            await ctx.send(
                "JANUS: No zones registered in zone state. Run `!reset_all` or add zones before using `!impact`."
            )
            return

        k = min(len(available), random.randint(2, 4))
        impacted = random.sample(available, k)
                
        for zone in impacted:
            zone_states[zone] = "Damaged"
        save_zone_states()
        report = "\n".join([f"⚠️ {z} — Damaged" for z in impacted])
        await ctx.send(f"JANUS: External collision registered. Impact cause: {cause.title()}.\n"
                    f"JANUS: Systems destabilized. Damage assessment complete.\n\n{report}")

    # --- Crew & Ship Systems Commands ---
    @bot.command(name="crew")
    async def crew_command(ctx):
        crew_info = ship_profile["crew"]
        shifts = crew_info["rotation_protocol"]["shift_structure"]
        
        embed = discord.Embed(
            title="Crew Operations — Shift & Rotation Protocol",
            description=(
                f"Max crew: **{crew_info['maximum_complement']}**\n"
                f"Min operational: **{crew_info['minimum_operational_crew']}**\n\n"
                f"Teams: **{', '.join(crew_info['rotation_protocol']['crews'])}**\n"
                f"Shifts: **{shifts['active_hours']}h on / {shifts['rest_hours']}h off**\n"
                f"Extended break: **{shifts['monthly_extended_rest']}**\n"
                f"Off-duty procedure: {crew_info['rotation_protocol']['off_duty_procedure']}"
            ), 
            color=discord.Color.teal()
        )
        
        embed.set_footer(text="Erebus Corporation – Personnel Compliance Required")
        await ctx.send(embed=embed)
    @bot.command(name="ai")
    async def ai_command(ctx):
        await ctx.send(
        "JANUS: AI core online. Oversight active. Autonomy restricted per Erebus Corporation policy."
    )
    @bot.command(name="extractors")
    async def extractors_command(ctx):
        xsys = ship_profile["extraction_systems"]
        
        embed = discord.Embed(
            title="Extractor Unit Overview",
            description=(
                f"{ship_profile['ship_name']} is equipped with **{xsys['extractor_units']} Extractor Units**.\n\n"
                f"Technology: **{xsys['technology']}**\n\n"
                f"{xsys['description']}\n\n"
                f"Resource Targets: {', '.join(xsys['resource_targets'])}"
            ), 
            color=discord.Color.dark_gold()
        )
        
        embed.set_footer(text="Ore Recovery Certified — Erebus Industrial Mining Division")
        await ctx.send(embed=embed)

def setup(bot):
    @bot.command(name="event")
    async def event_command(ctx, *, description: str = "random"):
            # Only allow this from the root command channel
        if ctx.channel.id != ROOT_COMMAND_CHANNEL_ID:
            return
        crew_channel = ctx.bot.get_channel(CREW_TERMINAL_CHANNEL_ID)
        if not crew_channel:
            await ctx.send("JANUS: Error. Crew terminal channel not configured.")
            return

        raw = (description or "").strip()
        parts = raw.split(maxsplit=1)

        priority = (parts[0].lower() if parts else "low")
        requested_title = (parts[1].strip() if len(parts) > 1 else None)

        if priority in ("", "random"):
            priority = "low"
            requested_title = None

        known_priorities = {str(d.get("priority", "")).strip().lower() for d in erebus_directives}

        if priority in known_priorities:
            pool = [d for d in erebus_directives if str(d.get("priority", "")).strip().lower() == priority]

            if not pool:
                message = "JANUS: No directives available at requested priority level."
            elif requested_title:
                matches = [d for d in pool if str(d.get("title", "")).strip().lower() == requested_title.lower()]
                if not matches:
                    message = "JANUS: Requested directive not found at specified priority level."
                else:
                    message = format_directive(matches[0])
            else:
                directive = random.choice(pool)
                message = format_directive(directive)
        else:
            message = f"JANUS: {description}"

        await crew_channel.send(message)
        await ctx.message.add_reaction("✅")

    # --- Alert System Command ---
    @bot.command(name="alert")
    async def alert_command(ctx):
        alert_lines = [
            "Red Alert. Ship systems compromised.",
            "Security advisory: containment breach possible.",
            "Environmental hazard detected. Evacuate affected zones.",
            "Warning. Subsystems unstable. Proceed with caution.",
            "Attention. Catastrophic failure in progress."
        ]
        line = random.choice(alert_lines)
        await ctx.send(f"JANUS: {line}")

    # --- Help Commands ---
    @bot.command(name="help_commands")
    async def help_commands_command(ctx):
        embed = discord.Embed(
            title="Command Reference",
            description="Available commands for the Persephone bot.",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Crew Commands", value=(
            "`!ship`\n"
            "`!ship [room]`\n"
            "`!crew`\n"
            "`!ai`\n"
            "`!extractors`\n"
            "`!status`\n"
            "`!report`\n"
            "`!rooms`\n"
            "`!deckplan`\n"
            "`!whereis [zone]`\n"
        ), inline=False)

        embed.add_field(name="JANUS AI Queries", value=(
            "`!janus diagnostics`\n"
            "`!janus ore status`\n"
            "`!janus life support`\n"
            "`!janus power status`\n"
            "`!janus mission status`\n"
            "`!janus maintenance log`\n"
            "`!janus corporate message`\n"
            "`!janus crew status`\n"
            "`!janus survey`\n"
            "`!janus analyze artifact`"
        ), inline=False)

        embed.add_field(name="System Control (DM Access)", value=(
            "`!damage <zone>`\n"
            "`!repair <zone>`\n"
            "`!lockdown <zone>`\n"
            "`!unlock <zone>`\n"
            "`!reset_all`\n"
            "`!impact [cause]`\n"
            "`!alert`"
        ), inline=False)

        embed.add_field(name="Voice System", value=(
            "`!join`\n"
            "`!leave`\n"
            "`!voice [code]`\n"
            "`!test [msg]`"
        ), inline=False)

        embed.set_footer(text="For internal use only — Erebus Corporation Property")
        await ctx.send(embed=embed)

    @bot.command(name="help_crew")
    async def help_crew_command(ctx):
        embed = discord.Embed(
            title="Crew Command Reference",
            description="JANUS access interface — Authorized personnel only",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Ship & Crew Systems", value=(
            "`!ship`\n"
            "`!ship [room]`\n"
            "`!crew`\n"
            "`!ai`\n"
            "`!extractors`\n"
            "`!status`\n"
            "`!report`\n"
            "`!rooms`\n"
            "`!deckplan`\n"
            "`!whereis [zone]`\n"
            
        ), inline=False)

        embed.add_field(name="JANUS AI Queries", value=(
            "`!janus diagnostics`\n"
            "`!janus ore status`\n"
            "`!janus life support`\n"
            "`!janus power status`\n"
            "`!janus mission status`\n"
            "`!janus maintenance log`\n"
            "`!janus corporate message`\n"
            "`!janus crew status`\n"
            "`!janus survey`\n"
            "`!janus analyze artifact`"
        ), inline=False)

        embed.set_footer(text="Erebus Corporation – Crew Access Tier 3")
        await ctx.send(embed=embed)

    @bot.command(name="help_ship")
    async def help_ship_command(ctx):
        # Now we create our own function to avoid calling another command function
        embed = discord.Embed(
            title="Persephone Systems Interface",
            description="Command Directory — Erebus Corporation Access Tier C",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Crew Commands", value=(
            "`!ship`\n"
            "`!ship [room]`\n"
            "`!crew`\n"
            "`!ai`\n"
            "`!extractors`\n"
            "`!status`\n"
            "`!report`\n"
            "`!rooms`\n"
            "`!deckplan`\n"
            "`!whereis [zone]`\n"
            
        ), inline=False)

        embed.add_field(name="JANUS AI Queries", value=(
            "`!janus diagnostics`\n"
            "`!janus ore status`\n"
            "`!janus life support`\n"
            "`!janus power status`\n"
            "`!janus mission status`\n"
            "`!janus maintenance log`\n"
            "`!janus corporate message`\n"
            "`!janus crew status`\n"
            "`!janus survey`\n"
            "`!janus analyze artifact`"
        ), inline=False)

        embed.add_field(name="System Control (DM Access)", value=(
            "`!damage <zone>`\n"
            "`!repair <zone>`\n"
            "`!lockdown <zone>`\n"
            "`!unlock <zone>`\n"
            "`!reset_all`\n"
            "`!impact [cause]`\n"
            "`!alert`"
        ), inline=False)

        embed.add_field(name="Voice System", value=(
            "`!join`\n"
            "`!leave`\n"
            "`!voice [code]`\n"
            "`!test [msg]`"
        ), inline=False)

        embed.set_footer(text="For internal use only — Erebus Corporation Property")
        await ctx.send(embed=embed)

    # Don't forget to implement whereis command which is mentioned in help but not defined
    @bot.command(name="whereis")
    async def whereis_command(ctx, *, zone=None):
        if not zone:
            await ctx.send("Specify a zone to locate. Example: `!whereis medbay`")
            return
            
        real_zone = resolve_zone(zone)
        if real_zone:
            deck = next((z.get("deck") for z in ship_profile["ship_zones"] if z["zone_name"] == real_zone), "Unknown")
            links = ZONE_CONNECTIONS.get(real_zone, [])
            links_text = ", ".join(links) if links else "No connection data."
            await ctx.send(
                f"JANUS: {real_zone}. Deck: {deck}. Access: {links_text}."
)
