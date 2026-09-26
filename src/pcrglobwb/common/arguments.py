import re

# one table for both models, so a coupled run passes the same flag and value to
# PCR-GLOBWB's ini and QUAlloc's cfg
PLACEHOLDER_FLAGS = {
    "--output-dir": ("MAIN_OUTPUT_DIR", "main output directory"),
    "--input-dir": ("MAIN_INPUT_DIR", "main input directory"),
    "--start-date": ("START_DATE", "start date"),
    "--end-date": ("END_DATE", "end date"),
    "--initial-state-dir": ("MAIN_INITIAL_STATE_FOLDER", "initial states folder"),
    "--initial-state-date": ("DATE_FOR_INITIAL_STATES", "initial states date"),
    "--clone-connections": ("CLONE_CONNECTIONS", "clone connections"),
    "--precipitation-file": ("PRECIPITATION_FORCING_FILE", "precipitation forcing"),
    "--temperature-file": ("TEMPERATURE_FORCING_FILE", "temperature forcing"),
    "--ref-pot-et-file": ("REF_POT_ET_FORCING_FILE", "reference potential ET forcing"),
    "--pressure-file": ("PRESSURE_FORCING_FILE", "pressure forcing"),
    "--wind-file": ("WIND_FORCING_FILE", "wind forcing"),
    "--shortwave-radiation-file": (
        "SHORTWAVE_RADIATION_FORCING_FILE",
        "shortwave radiation forcing",
    ),
    "--relative-humidity-file": (
        "RELATIVE_HUMIDITY_FORCING_FILE",
        "relative humidity forcing",
    ),
    "--baseflow-exponent": ("BASEFLOW_EXP_INPUT", "groundwater baseflow exponent"),
    "--spinup-years": ("NUMBER_OF_SPINUP_YEARS", "number of spin-up years"),
    "--clone-map": ("CLONEMAP", "clone map"),
    "--use-max-fossil-gw-ini": (
        "USE_MAXIMUM_STOR_GROUNDWATER_FOSSIL_INI",
        "useMaximumStorGroundwaterFossilIni",
    ),
    "--estimate-gw-ini-from-recharge": (
        "ESTIMATE_STOR_GROUNDWATER_INI_FROM_RECHARGE",
        "estimateStorGroundwaterIniFromRecharge",
    ),
    "--daily-gw-recharge-ini": (
        "DAILY_GROUNDWATER_RECHARGE_INI",
        "dailyGroundwaterRechargeIni",
    ),
    "--qualloc-config": ("QUALLOC_CONFIG_FILE", "QUAlloc cfg file"),
    "--pcrglobwb-output-dir": (
        "PCRGLOBWB_OUTPUT_DIR",
        "output directory of the PCR-GLOBWB run to read",
    ),
}


def add_placeholder_arguments(parser, flags):
    """Add each flag, storing its value under the name of the placeholder it fills."""
    for flag in flags:
        token, description = PLACEHOLDER_FLAGS[flag]
        parser.add_argument(flag, dest=token, help=description)


def placeholder_values(args, flags):
    """Return {placeholder: value} for the flags given on the command line."""
    tokens = [PLACEHOLDER_FLAGS[flag][0] for flag in flags]
    return {
        token: getattr(args, token)
        for token in tokens
        if getattr(args, token) is not None
    }


def fill_placeholders(text, replacements, flags, source):
    """Replace the placeholders of ``flags`` in ``text`` with their ``replacements``.

    Placeholders match as whole words. Raises ValueError if ``text`` uses one
    that has no replacement, as it would otherwise surface much later as a
    missing file.
    """
    names = {PLACEHOLDER_FLAGS[flag][0]: flag for flag in flags}
    pattern = re.compile(r"\b(%s)\b" % "|".join(names))
    missing = sorted(set(pattern.findall(text)) - set(replacements))
    if missing:
        raise ValueError(
            "%s uses placeholders with no value; pass %s"
            % (source, ", ".join("%s (%s)" % (names[t], t) for t in missing))
        )
    return pattern.sub(lambda match: replacements[match.group(1)], text)
