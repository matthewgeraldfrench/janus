import os
import json
import random
import discord
from discord.ext import commands
from difflib import get_close_matches

# IDs for DM control and crew-facing terminal
ROOT_COMMAND_CHANNEL_ID = 1350826672504700938# replace with your #root-command channel ID
CREW_TERMINAL_CHANNEL_ID = 1350922295782281297# IDs for DM control and crew-facing terminal

# --- File and Directory Setup ---
base_dir = os.path.dirname(os.path.abspath(__file__))
zone_state_path = os.path.join(base_dir, "zone_state.json")

# --- Data Loading ---
with open(os.path.join(base_dir, "ship_data.json"), "r") as file:
    ship_profile = json.load(file)

try:
    with open(zone_state_path, "r") as f:
        zone_states = json.load(f)
except FileNotFoundError:
    zone_states = {}

# --- Helper Functions ---
def save_zone_states():
    """Save the current zone states to the JSON file."""
    with open(zone_state_path, "w") as f:
        json.dump(zone_states, f, indent=4)

erebus_directives = [
    {
        "title": "Conduit Performance Verification",
        "location": "Main Engineering / Maintenance Shafts",
        "summary": "Minor power fluctuations detected in aging conduits. Verify structural and electrical integrity to prevent future inefficiencies.",
        "priority": "Low",
        "compliance": "Documentation of inspection is required for maintenance records."
    },
    {
        "title": "Asset Retrieval — Maintenance Drone",
        "location": "Drone Hangar & Cargo Access",
        "summary": "A maintenance drone failed standard check-in procedures. Locate, secure, and return the unit for reformatting.",
        "priority": "Moderate",
        "compliance": "Drone hardware is Erebus property and must not be abandoned."
    },
    {
        "title": "Cryostasis Unit Temperature Variance",
        "location": "Crew Quarters & Cryostasis Wing",
        "summary": "A cryo-chamber reports a minor but persistent temperature drift. Recalibrate to maintain personnel preservation standards.",
        "priority": "Elevated",
        "compliance": "Deviations affecting frozen personnel will be reviewed by Human Resources."
    },
    {
        "title": "Unregistered Material Analysis",
        "location": "Ore Intake & Analysis Lab",
        "summary": "An ore container exhibits unexpected spectrographic markers not present in cargo inventory. Conduct corporate-aligned analysis.",
        "priority": "Moderate",
        "compliance": "Unauthorized discovery claims will not be recognized by Erebus Corporation."
    },
    {
        "title": "Cargo Stabilization Procedure",
        "location": "Primary Cargo Hold",
        "summary": "Gravity variance caused displacement of secured containers. Realign cargo and restore safe operational pathways.",
        "priority": "Low",
        "compliance": "Do not open containers without Level 3 authorization."
    },
    {
        "title": "Coolant Integrity Inspection",
        "location": "Refining & Processing Deck",
        "summary": "Vaporized coolant detected in refinery subsystems. Trace origin, repair leaks, and restore nominal flow.",
        "priority": "Moderate",
        "compliance": "Coolant waste will be logged against ship efficiency metrics."
    },
    {
        "title": "Personnel Noncompliance Review",
        "location": "Last Known Duty Station",
        "summary": "A crew member failed to report at scheduled shift change. Locate, assess, and return employee to assigned duties.",
        "priority": "Low",
        "compliance": "Attendance deviations may affect performance evaluations."
    },
    {
        "title": "Internal Signal Audit",
        "location": "Command Bridge / Communications Station",
        "summary": "An unscheduled communications ping was detected originating from within the Persephone. Identify and isolate signal source.",
        "priority": "Elevated",
        "compliance": "Unregistered signals are treated as potential security violations."
    },
]


# Zone name resolution system
zone_aliases = {
    "core": "C.O.R.E. — Central Operations for Resource Extraction",
    "bridge": "Command Bridge",
    "engineering": "Main Engineering",
    "extractors": "Extractor Control Station",
    "drone bay": "Drone Hangar & Fabrication Bay",
    "lab": "Ore Intake & Analysis Lab",
    "refinery": "Refining & Processing Deck",
    "cargo": "Cargo Hold",
    "cryo": "Crew Quarters & Cryostasis Wing",
    "galley": "Galley & Recreation Hall",
    "medbay": "Medical Bay",
    "maintenance": "Maintenance Access & System Shafts"
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
    @bot.command(name="ship")
    async def ship_command(ctx, *, topic=None):
        if topic is None:
            # Display general ship information
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

        # Display information about a specific room/zone
        topic = topic.lower()
        room_names = [zone["zone_name"].lower() for zone in ship_profile["ship_zones"]]
        match = get_close_matches(topic, room_names, n=1, cutoff=0.4)

        if match:
            for zone in ship_profile["ship_zones"]:
                if zone["zone_name"].lower() == match[0]:
                    embed = discord.Embed(
                        title=zone["zone_name"],
                        description=zone["description"],
                        color=discord.Color.orange()
                    )
                    embed.set_footer(text=f"{ship_profile['ship_name']} — Erebus Corp Resource Harvester")
                    await ctx.send(embed=embed)
                    return

        await ctx.send("No match found. Try `!ship core`, `!ship medbay`, or `!help_ship`.")

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

    @bot.command(name="map")
    async def map_command(ctx):
        image_path = os.path.join(base_dir, "persephone_2d.png")
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                file = discord.File(f, filename="persephone_2d.png")
                await ctx.send("JANUS: Deck schematic interface active. Uploading visual layout...", file=file)
        else:
            await ctx.send("JANUS: Schematic file not found. Ensure 'persephone_2d.png' exists in the same folder.")

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
            await ctx.send(f"JANUS: {real_zone} integrity compromised. Engineering response required.")
        else:
            await ctx.send("JANUS: Zone not recognized. Try `!status`, `!ship`, or `!help_ship`.")

    @bot.command(name="repair")
    async def repair_command(ctx, *, zone=None):
        if not zone:
            await ctx.send("Specify a zone to repair. Example: `!repair medbay`")
            return
            
        real_zone = resolve_zone(zone)
        if real_zone:
            zone_states[real_zone] = "Online"
            save_zone_states()
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
            await ctx.send(f"JANUS: Lockdown lifted for {real_zone}. Zone access restored.")
        else:
            await ctx.send("JANUS: Zone not recognized. Try `!status`, `!ship`, or `!help_ship`.")

    @bot.command(name="reset_all")
    async def reset_all_command(ctx):
        for zone in zone_states:
            zone_states[zone] = "Online"
        save_zone_states()
        await ctx.send("JANUS: All ship zones restored to nominal status. Maintenance backlog cleared.")

    @bot.command(name="impact")
    async def impact_command(ctx, *, cause="asteroid"):
        impacted = random.sample(list(zone_states.keys()), random.randint(2, 4))
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
        ai_data = ship_profile["ai_core"]
        
        embed = discord.Embed(
            title="AI Core — JANUS",
            description=(
                f"**Janus** oversees full ship functionality.\n\n"
                f"Integration: {ai_data['integration']}\n"
                f"Autonomy: {ai_data['operational_capability']}\n"
                f"Core Location: {ai_data['core_location']}"
            ),
            color=discord.Color.purple()
        )
        
        embed.set_footer(text="Janus Core Certified – Erebus Systems Division")
        await ctx.send(embed=embed)

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
        await ctx.bot.speak_alert(ctx, random.choice(alert_lines))
        await ctx.send("JANUS: Vocal alert broadcast complete.")
        
    @bot.command(name="event")
    async def event_command(ctx, *, description: str):
        # Only allow this from the root command channel
        if ctx.channel.id != ROOT_COMMAND_CHANNEL_ID:
            return

        crew_channel = ctx.bot.get_channel(CREW_TERMINAL_CHANNEL_ID)
        if crew_channel:
            if description.strip().lower() == "random":
                directive = random.choice(erebus_directives)
                message = format_directive(directive)
            else:
                # Otherwise, treat it as a manual JANUS line
                message = f"JANUS: {description}"
                        
            await crew_channel.send(f"JANUS: {description}")
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send("JANUS: Error. Crew terminal channel not configured.")


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
            "`!map`"
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
            "`!map`"
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
            "`!map`"
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
            # This implementation will need to be updated with actual location data when available
            await ctx.send(f"JANUS: {real_zone} location highlighted on ship schematic. Use `!map` to view.")
        else:
            await ctx.send("JANUS: Zone not recognized. Try `!rooms` for a list of valid zones.")