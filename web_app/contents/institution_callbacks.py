"""Callbacks for institution-related controls. """

import dataclasses as dc
import logging
from typing import Dict, List

import universal_utils.types as uut
from dash import no_update  # type: ignore[import]
from dash.dependencies import Input, Output, State  # type: ignore[import]

from ..config import app
from ..data_source import data_source as src
from ..data_source import institution_info
from ..data_source.utils import DataSourceException
from ..utils import dash_utils as du
from ..utils.oidc_tools import CurrentUser


@dc.dataclass
class SelectInstitutionValueOutput:
    """Outputs for select_institution_value()."""

    urlpath: str = no_update
    # VALUES
    phds_val: int | None = no_update
    faculty_val: int | None = no_update
    scis_val: int | None = no_update
    grads_val: int | None = no_update
    cpus_val: int | None = no_update
    gpus_val: int | None = no_update
    textarea_val: str = no_update
    # LABELS
    h2_table: str = no_update
    h2_textarea: str = no_update
    h2_computing: str = no_update
    # CONTAINERS FOR HIDING
    headcounts_container_hidden: bool = no_update
    conf_table_hidden: bool = no_update
    below_table_container_hidden: bool = no_update
    # INST DROPDOWN
    ddown_inst_val: str = no_update
    ddown_inst_opts: List[Dict[str, str]] = no_update
    # LABOR
    # labor_opts: List[Dict[str, str]] = no_update
    # INST-VAL STORES
    # conf_init: dict = no_update
    conf_headcounts: dict = no_update
    conf_table: dict = no_update
    conf_computing: dict = no_update
    # INST-VAL CONFIRMATION BUTTONS
    conf_headcounts_btn_icon_class: str = no_update
    conf_headcounts_btn_label_text: str = no_update
    conf_headcounts_btn_classname: str = no_update
    conf_table_btn_icon_class: str = no_update
    conf_table_btn_label_text: str = no_update
    conf_table_btn_classname: str = no_update
    conf_computing_btn_icon_class: str = no_update
    conf_computing_btn_label_text: str = no_update
    conf_computing_btn_classname: str = no_update

    def update_institution_values(self, inst_vals: uut.InstitutionValues) -> None:
        """Updated fields using/dependent on `InstitutionValues` instance."""
        self.phds_val = inst_vals.phds_authors
        self.faculty_val = inst_vals.faculty
        self.scis_val = inst_vals.scientists_post_docs
        self.grads_val = inst_vals.grad_students
        self.cpus_val = inst_vals.cpus if inst_vals.cpus else 0  # None (blank) -> 0
        self.gpus_val = inst_vals.gpus if inst_vals.gpus else 0  # None (blank) -> 0
        self.textarea_val = inst_vals.text
        self.conf_headcounts = dc.asdict(inst_vals.headcounts_metadata)
        self.conf_table = dc.asdict(inst_vals.table_metadata)
        self.conf_computing = dc.asdict(inst_vals.computing_metadata)

        # Headcounts button styling
        if inst_vals.headcounts_metadata.has_valid_confirmation():
            self.conf_headcounts_btn_icon_class = du.IconClassNames.CHECK_TO_SLOT
            self.conf_headcounts_btn_label_text = "Confirmed"
            self.conf_headcounts_btn_classname = (
                du.ButtonIconLabelTooltipFactory.build_classname(
                    outline=False, color=du.Color.SUCCESS
                )
            )
        else:
            self.conf_headcounts_btn_icon_class = du.IconClassNames.RIGHT_TO_BRACKET
            self.conf_headcounts_btn_label_text = "Confirm"
            self.conf_headcounts_btn_classname = (
                du.ButtonIconLabelTooltipFactory.build_classname(
                    outline=True, color=du.Color.SUCCESS
                )
            )
        # Table button styling
        if inst_vals.table_metadata.has_valid_confirmation():
            self.conf_table_btn_icon_class = du.IconClassNames.CHECK_TO_SLOT
            self.conf_table_btn_label_text = "All Statements of Work are Confirmed"
            self.conf_table_btn_classname = (
                du.ButtonIconLabelTooltipFactory.build_classname(
                    outline=False, color=du.Color.SUCCESS
                )
            )
        else:
            self.conf_table_btn_icon_class = du.IconClassNames.RIGHT_TO_BRACKET
            self.conf_table_btn_label_text = "Confirm All Statements of Work"
            self.conf_table_btn_classname = (
                du.ButtonIconLabelTooltipFactory.build_classname(
                    outline=True, color=du.Color.SUCCESS
                )
            )
        # Computing button styling
        if inst_vals.computing_metadata.has_valid_confirmation():
            self.conf_computing_btn_icon_class = du.IconClassNames.CHECK_TO_SLOT
            self.conf_computing_btn_label_text = "Confirmed"
            self.conf_computing_btn_classname = (
                du.ButtonIconLabelTooltipFactory.build_classname(
                    outline=False, color=du.Color.SUCCESS
                )
            )
        else:
            self.conf_computing_btn_icon_class = du.IconClassNames.RIGHT_TO_BRACKET
            self.conf_computing_btn_label_text = "Confirm"
            self.conf_computing_btn_classname = (
                du.ButtonIconLabelTooltipFactory.build_classname(
                    outline=True, color=du.Color.SUCCESS
                )
            )


@dc.dataclass(frozen=True)
class SelectInstitutionValueState:
    """States for select_institution_value()."""

    s_urlpath: str
    s_snap_ts: str
    s_table: uut.WebTable
    # INST-VAL STORES
    # s_conf_init: dict
    s_conf_headcounts: dict
    s_conf_table: dict
    s_conf_computing: dict


@dc.dataclass(frozen=True)
class SelectInstitutionValueInputs:
    """Inputs for select_institution_value()."""

    inst_val: str | None
    # INST VALUES
    # user/setup_institution_components()
    phds_val: int | None
    faculty_val: int | None
    scis_val: int | None
    grads_val: int | None
    cpus_val: int | None
    gpus_val: int | None
    textarea_val: str | None
    # CLICKS
    # user-only
    comfirm_headcounts_click: int
    comfirm_table_click: int
    comfirm_computing_click: int
    # INTERVALS
    n_interval_trigger_conf_refresh: int

    def get_institution_values(
        self, state: SelectInstitutionValueState
    ) -> uut.InstitutionValues:
        """Get an `InstitutionValues` instance from fields and `state`."""
        headcounts_metadata = uut.InstitutionAttrMetadata(
            **state.s_conf_headcounts,
        )
        table_metadata = uut.InstitutionAttrMetadata(
            **state.s_conf_table,
        )
        computing_metadata = uut.InstitutionAttrMetadata(
            **state.s_conf_computing,
        )

        return uut.InstitutionValues(
            phds_authors=self.phds_val,
            faculty=self.faculty_val,
            scientists_post_docs=self.scis_val,
            grad_students=self.grads_val,
            cpus=self.cpus_val,
            gpus=self.gpus_val,
            text=self.textarea_val if self.textarea_val else "",
            headcounts_metadata=headcounts_metadata,
            table_metadata=table_metadata,
            computing_metadata=computing_metadata,
        )


@app.callback(  # type: ignore[misc]
    output=dc.asdict(
        SelectInstitutionValueOutput(
            # URL
            urlpath=Output("url", "pathname"),
            # VALUES
            phds_val=Output("wbs-phds-authors", "value"),
            faculty_val=Output("wbs-faculty", "value"),
            scis_val=Output("wbs-scientists-post-docs", "value"),
            grads_val=Output("wbs-grad-students", "value"),
            cpus_val=Output("wbs-cpus", "value"),
            gpus_val=Output("wbs-gpus", "value"),
            textarea_val=Output("wbs-textarea", "value"),
            # LABELS
            h2_table=Output("wbs-h2-sow-table", "children"),
            h2_textarea=Output("wbs-h2-inst-textarea", "children"),
            h2_computing=Output("wbs-h2-inst-computing", "children"),
            # CONTAINERS FOR HIDING
            headcounts_container_hidden=Output(
                "institution-headcounts-container", "hidden"
            ),
            conf_table_hidden=Output("wbs-table-confirm-yes", "hidden"),
            below_table_container_hidden=Output(
                "institution-values-below-table-container", "hidden"
            ),
            # INST DROPDOWN
            ddown_inst_val=Output("wbs-dropdown-institution", "value"),
            ddown_inst_opts=Output("wbs-dropdown-institution", "options"),
            # LABOR
            # labor_opts=Output("wbs-filter-labor", "options"),
            # INST-VAL STORES
            # conf_init=Output("wbs-store-confirm-initial", "data"),
            # instval_conf=Output("wbs-store-confirm", "data"),
            conf_headcounts=Output("wbs-store-confirm-headcounts", "data"),
            conf_table=Output("wbs-store-confirm-table", "data"),
            conf_computing=Output("wbs-store-confirm-computing", "data"),
            # INST-VAL CONFIRMATION BUTTONS
            conf_headcounts_btn_icon_class=Output(
                "wbs-headcounts-confirm-yes-i", "className"
            ),
            conf_headcounts_btn_label_text=Output(
                "wbs-headcounts-confirm-yes-label", "children"
            ),
            conf_headcounts_btn_classname=Output(
                "wbs-headcounts-confirm-yes", "className"
            ),
            conf_table_btn_icon_class=Output("wbs-table-confirm-yes-i", "className"),
            conf_table_btn_label_text=Output("wbs-table-confirm-yes-label", "children"),
            conf_table_btn_classname=Output("wbs-table-confirm-yes", "className"),
            conf_computing_btn_icon_class=Output(
                "wbs-computing-confirm-yes-i", "className"
            ),
            conf_computing_btn_label_text=Output(
                "wbs-computing-confirm-yes-label", "children"
            ),
            conf_computing_btn_classname=Output(
                "wbs-computing-confirm-yes", "className"
            ),
        )
    ),
    inputs=dict(
        inputs=dc.asdict(
            SelectInstitutionValueInputs(
                # INST DROPDOWN
                # user/setup_institution_components
                inst_val=Input("wbs-dropdown-institution", "value"),
                # INST VALUES
                # user/setup_institution_components()
                phds_val=Input("wbs-phds-authors", "value"),
                faculty_val=Input("wbs-faculty", "value"),
                scis_val=Input("wbs-scientists-post-docs", "value"),
                grads_val=Input("wbs-grad-students", "value"),
                cpus_val=Input("wbs-cpus", "value"),
                gpus_val=Input("wbs-gpus", "value"),
                textarea_val=Input("wbs-textarea", "value"),
                # CLICKS
                # user-only
                comfirm_headcounts_click=Input(
                    "wbs-headcounts-confirm-yes", "n_clicks"
                ),
                comfirm_table_click=Input("wbs-table-confirm-yes", "n_clicks"),
                comfirm_computing_click=Input("wbs-computing-confirm-yes", "n_clicks"),
                # INTERVALS
                n_interval_trigger_conf_refresh=Input(
                    "wbs-interval-trigger-confirmation-refreshes", "n_intervals"
                ),
            )
        )
    ),
    state=dict(
        state=dc.asdict(
            SelectInstitutionValueState(
                s_urlpath=State("url", "pathname"),
                s_snap_ts=State("wbs-current-snapshot-ts", "value"),
                s_table=State("wbs-data-table", "data"),
                # s_conf_init=Output("wbs-store-confirm-initial", "data"),
                # s_instval_conf=Output("wbs-store-confirm", "data"),
                s_conf_headcounts=State("wbs-store-confirm-headcounts", "data"),
                s_conf_table=State("wbs-store-confirm-table", "data"),
                s_conf_computing=State("wbs-store-confirm-computing", "data"),
            )
        )
    ),
    # prevent_initial_call=True,
)
def select_institution_value(inputs: dict, state: dict) -> dict:
    """For all things institution values"""
    return dc.asdict(
        _select_institution_value_dc(
            SelectInstitutionValueInputs(**inputs),
            SelectInstitutionValueState(**state),
        )
    )


def _select_institution_value_dc(
    inputs: SelectInstitutionValueInputs,
    state: SelectInstitutionValueState,
) -> SelectInstitutionValueOutput:
    logging.warning(
        f"'{du.triggered()}' -> select_institution_value() ({state.s_urlpath=} {state.s_snap_ts=} {CurrentUser.get_summary()=})"
    )

    match du.triggered():
        # initial_call
        case ".":
            try:
                du.precheck_setup_callback(state.s_urlpath)
            except du.CallbackAbortException as e:
                logging.critical(f"ABORTED: select_institution_value() [{e}]")
                return SelectInstitutionValueOutput()
            return to_pull_institution_values(inputs, state)
        # INTERVALS
        case "wbs-interval-trigger-confirmation-refreshes.n_intervals":
            return to_pull_institution_values(inputs, state)
        # INST DROPDOWN
        case "wbs-dropdown-institution.value":
            return changed_institution(inputs, state)
        # INST VALUES
        case (
            "wbs-phds-authors.value"
            | "wbs-faculty.value"
            | "wbs-scientists-post-docs.value"
            | "wbs-grad-students.value"
            | "wbs-cpus.value"
            | "wbs-gpus.value"
            | "wbs-textarea.value"
        ):
            return to_push_institution_values(inputs, state)
        # CLICKS
        case (
            "wbs-headcounts-confirm-yes.n_clicks"
            | "wbs-table-confirm-yes.n_clicks"
            | "wbs-computing-confirm-yes.n_clicks"
        ):
            return to_confirm_institution_values(inputs, state)

    raise ValueError(f"Unaccounted for trigger: {du.triggered()}")


def changed_institution(
    inputs: SelectInstitutionValueInputs,
    state: SelectInstitutionValueState,
) -> SelectInstitutionValueOutput:
    """Refresh if the user selected a different institution."""
    logging.info("changed_institution")

    # did anything change?
    if inputs.inst_val is None and du.get_inst(state.s_urlpath) == "":
        return SelectInstitutionValueOutput()
    if inputs.inst_val == du.get_inst(state.s_urlpath):
        return SelectInstitutionValueOutput()

    return SelectInstitutionValueOutput(
        urlpath=du.build_urlpath(du.get_wbs_l1(state.s_urlpath), inputs.inst_val)
    )


def to_pull_institution_values(
    inputs: SelectInstitutionValueInputs,
    state: SelectInstitutionValueState,
) -> SelectInstitutionValueOutput:
    logging.info("to_pull_institution_values")

    output = SelectInstitutionValueOutput()

    def inactive_flag(info: institution_info.Institution) -> str:
        if info.has_mou:
            return ""
        return "inactive: "

    # institution dropdown
    if CurrentUser.is_admin():
        output.ddown_inst_opts = [  # always include the abbreviations for admins
            {
                "label": f"{inactive_flag(info)}{short_name} ({info.long_name})",
                "value": short_name,
                # "disabled": not info.has_mou,
            }
            for short_name, info in institution_info.get_institutions_infos().items()
        ]
    else:
        output.ddown_inst_opts = [  # only include the user's institution(s)
            {
                "label": inactive_flag(info) + short_name,
                "value": short_name,
                # "disabled": not info.has_mou,
            }
            for short_name, info in institution_info.get_institutions_infos().items()
            if short_name in CurrentUser.get_institutions()
        ]
    output.ddown_inst_opts = sorted(output.ddown_inst_opts, key=lambda d: d["label"])

    # labor dropdown
    # output.labor_opts = [
    #     {"label": f"{abbrev} – {name}", "value": abbrev}
    #     for name, abbrev in tconfig.get_labor_categories_w_abbrevs()
    # ]

    # are we looking at an institution?
    if inst := du.get_inst(state.s_urlpath):
        output.h2_table = f"{inst}'s Statements of Work"
        output.h2_textarea = f"{inst}'s Miscellaneous Notes and Descriptions"
        output.h2_computing = f"{inst}'s Computing Contributions"
        try:
            output.update_institution_values(
                src.pull_institution_values(
                    du.get_wbs_l1(state.s_urlpath),
                    state.s_snap_ts,
                    inst,
                )
            )
        except DataSourceException:
            output.update_institution_values(uut.InstitutionValues())
    else:  # we're looking at the collaboration-view
        output.h2_table = "Collaboration-Wide Statements of Work"
        output.h2_textarea = ""
        output.h2_computing = ""
    output.ddown_inst_val = inst

    # hide inst-vals if not M&O
    if not inst or du.get_wbs_l1(state.s_urlpath) != "mo":
        output.headcounts_container_hidden = True
        output.conf_table_hidden = True
        output.below_table_container_hidden = True
    else:
        output.headcounts_container_hidden = False
        output.conf_table_hidden = False
        output.below_table_container_hidden = False

    return output


# @app.callback(  # type: ignore[misc]
#     [
#         Output("wbs-phds-authors", "value"),
#         Output("wbs-faculty", "value"),
#         Output("wbs-scientists-post-docs", "value"),
#         Output("wbs-grad-students", "value"),
#         Output("wbs-cpus", "value"),
#         Output("wbs-gpus", "value"),
#         Output("wbs-textarea", "value"),
#         #
#         Output("wbs-h2-sow-table", "children"),
#         Output("wbs-h2-inst-textarea", "children"),
#         Output("wbs-h2-inst-computing", "children"),
#         #
#         Output("institution-headcounts-container", "hidden"),
#         Output("institution-values-below-table-container", "hidden"),
#         #
#         Output("wbs-dropdown-institution", "value"),
#         Output("wbs-dropdown-institution", "options"),
#         #
#         Output("wbs-filter-labor", "options"),
#         #
#         Output("wbs-store-confirm-initial", "data"),
#         Output("wbs-store-confirm", "data"),
#     ],
#     [Input("dummy-input-for-setup", "hidden")],  # never triggered
#     [
#         State("url", "pathname"),
#         State("wbs-current-snapshot-ts", "value"),
#     ],
# )
# def setup_institution_components(
#     _: bool,
#     # state(s)
#     s_urlpath: str,
#     s_snap_ts: types.DashVal,
# ) -> Tuple[
#     types.DashVal,
#     types.DashVal,
#     types.DashVal,
#     types.DashVal,
#     types.DashVal,
#     types.DashVal,
#     str,
#     #
#     str,
#     str,
#     str,
#     #
#     bool,
#     bool,
#     #
#     types.DashVal,
#     List[Dict[str, str]],
#     #
#     List[Dict[str, str]],
#     #
#     int,
#     int,
#     int,
# ]:
#     """Set up institution-related components."""
#     try:
#         du.precheck_setup_callback(s_urlpath)
#     except du.CallbackAbortException as e:
#         logging.critical(f"ABORTED: setup_institution_components() [{e}]")
#         return tuple(no_update for _ in range(17))  # type: ignore[return-value]
#     else:
#         logging.warning(
#             f"'{du.triggered()}' -> setup_institution_components() ({s_urlpath=} {s_snap_ts=} {CurrentUser.get_summary()=})"
#         )

#     inst_dc = uut.InstitutionValues(
#         phds_authors=0,
#         faculty=0,
#         scientists_post_docs=0,
#         grad_students=0,
#         cpus=0,
#         gpus=0,
#         text="",
#         headcounts_confirmed_ts=0,
#         table_confirmed_ts=0,
#         computing_confirmed_ts=0,
#     )

#     h2_table = "Collaboration-Wide SOW Table"
#     h2_textarea = ""
#     h2_computing = ""

#     wbs_l1 = du.get_wbs_l1(s_urlpath)
#     tconfig = tc.TableConfigParser(wbs_l1)

#     def inactive_flag(info: institution_info.Institution) -> str:
#         if info.has_mou:
#             return ""
#         return "inactive: "

#     if CurrentUser.is_admin():
#         inst_options = [  # always include the abbreviations for admins
#             {
#                 "label": f"{inactive_flag(info)}{short_name} ({info.long_name})",
#                 "value": short_name,
#                 # "disabled": not info.has_mou,
#             }
#             for short_name, info in institution_info.get_institutions_infos().items()
#         ]
#     else:
#         inst_options = [  # only include the user's institution(s)
#             {
#                 "label": inactive_flag(info) + short_name,
#                 "value": short_name,
#                 # "disabled": not info.has_mou,
#             }
#             for short_name, info in institution_info.get_institutions_infos().items()
#             if short_name in CurrentUser.get_institutions()
#         ]

#     labor_options = [
#         {"label": f"{abbrev} – {name}", "value": abbrev}
#         for name, abbrev in tconfig.get_labor_categories_w_abbrevs()
#     ]

#     if inst := du.get_inst(s_urlpath):
#         h2_table = f"{inst}'s SOW Table"
#         h2_textarea = f"{inst}'s Miscellaneous Notes and Descriptions"
#         h2_computing = f"{inst}'s Computing Contributions"
#         try:
#             inst_dc = src.pull_institution_values(wbs_l1, s_snap_ts, inst)
#         except DataSourceException:
#             inst_dc = uut.InstitutionValues(
#                 phds_authors=None,
#                 faculty=None,
#                 scientists_post_docs=None,
#                 grad_students=None,
#                 cpus=None,
#                 gpus=None,
#                 text="",
#                 headcounts_confirmed_ts=0,
#                 table_confirmed_ts=0,
#                 computing_confirmed_ts=0,
#             )

#     return (
#         inst_dc.phds_authors,
#         inst_dc.faculty,
#         inst_dc.scientists_post_docs,
#         inst_dc.grad_students,
#         inst_dc.cpus if inst_dc.cpus else 0,  # None (blank) -> 0
#         inst_dc.gpus if inst_dc.gpus else 0,  # None (blank) -> 0
#         inst_dc.text,
#         h2_table,
#         h2_textarea,
#         h2_computing,
#         not inst if wbs_l1 == "mo" else True,  # just hide it if not M&O
#         not inst if wbs_l1 == "mo" else True,  # just hide it if not M&O
#         inst,
#         sorted(inst_options, key=lambda d: d["label"]),
#         labor_options,
#         inst_dc.headcounts_confirmed_ts,
#         inst_dc.table_confirmed_ts,
#         inst_dc.computing_confirmed_ts,
#     )


# @app.callback(  # type: ignore[misc]
#     Output("url", "pathname"),
#     [Input("wbs-dropdown-institution", "value")],  # user/setup_institution_components
#     [State("url", "pathname")],
#     prevent_initial_call=True,
# )
# def select_dropdown_institution(inst: types.DashVal, s_urlpath: str) -> str:
#     """Refresh if the user selected an institution."""
#     logging.warning(
#         f"'{du.triggered()}' -> select_dropdown_institution() {inst=} {CurrentUser.get_institutions()=})"
#     )
#     inst = "" if not inst else inst

#     # did anything change?
#     if inst == du.get_inst(s_urlpath):
#         return no_update  # type: ignore[no-any-return]

#     return du.build_urlpath(du.get_wbs_l1(s_urlpath), inst)  # type: ignore[arg-type]


def institution_checks(state: SelectInstitutionValueState) -> str:
    # Is there an institution selected?
    if not (inst := du.get_inst(state.s_urlpath)):  # pylint: disable=C0325
        raise ValueError("No institution")

    # Are the fields editable?
    if not CurrentUser.is_loggedin_with_permissions():
        raise ValueError("Bad permissions / not logged in")

    # Is this a snapshot?
    if state.s_snap_ts:
        raise ValueError("Viewing a Snapshot")

    return inst


def to_confirm_institution_values(
    inputs: SelectInstitutionValueInputs,
    state: SelectInstitutionValueState,
) -> SelectInstitutionValueOutput:
    """Confirm inst values."""
    logging.info("to_confirm_institution_values")

    try:
        inst = institution_checks(state)
    except ValueError as e:
        logging.warning(f"Not allowed to confirm institution values: {e}")
        return SelectInstitutionValueOutput()

    # Get the inst vals
    inst_vals = inputs.get_institution_values(state)

    match du.triggered():
        # Confirm Headcounts
        case "wbs-headcounts-confirm-yes.n_clicks":
            # are we trying to confirm an already confirmed thing?
            if inst_vals.headcounts_metadata.has_valid_confirmation():
                logging.debug("ABORTED: Tried to re-confirm headcounts")
                return SelectInstitutionValueOutput()
            # confirm
            logging.debug(f"Confirming headcounts_metadata: {inst_vals}")
            inst_vals = src.confirm_institution_values(
                du.get_wbs_l1(state.s_urlpath), inst, headcounts=True
            )
        # Confirm Table
        case "wbs-table-confirm-yes.n_clicks":
            # are we trying to confirm an already confirmed thing?
            if inst_vals.table_metadata.has_valid_confirmation():
                logging.debug("ABORTED: Tried to re-confirm table")
                return SelectInstitutionValueOutput()
            # confirm
            logging.debug(f"Confirming table_metadata: {inst_vals}")
            inst_vals = src.confirm_institution_values(
                du.get_wbs_l1(state.s_urlpath), inst, table=True
            )
        # Confirm Computing
        case "wbs-computing-confirm-yes.n_clicks":
            # are we trying to confirm an already confirmed thing?
            if inst_vals.computing_metadata.has_valid_confirmation():
                logging.debug("ABORTED: Tried to re-confirm computing")
                return SelectInstitutionValueOutput()
            # confirm
            logging.debug(f"Confirming computing_metadata: {inst_vals}")
            inst_vals = src.confirm_institution_values(
                du.get_wbs_l1(state.s_urlpath), inst, computing=True
            )
        case _:
            raise ValueError(f"Unaccounted for trigger: {du.triggered()}")

    output = SelectInstitutionValueOutput()
    output.update_institution_values(inst_vals)
    return output


def to_push_institution_values(
    inputs: SelectInstitutionValueInputs,
    state: SelectInstitutionValueState,
) -> SelectInstitutionValueOutput:
    """Push inst values."""
    logging.info("to_push_institution_values")

    try:
        inst = institution_checks(state)
    except ValueError as e:
        logging.warning(f"Not allowed to push institution values: {e}")
        return SelectInstitutionValueOutput()

    # Get the inst vals
    inst_vals = inputs.get_institution_values(state)

    # push
    try:
        output = SelectInstitutionValueOutput()
        output.update_institution_values(
            src.push_institution_values(
                du.get_wbs_l1(state.s_urlpath),
                inst,
                inst_vals,
            )
        )
    except DataSourceException:
        assert len(state.s_table) == 0  # there's no collection to push to

    return output


# @app.callback(  # type: ignore[misc]
#     [
#         Output("wbs-institution-values-first-time-flag", "data"),
#         #
#         Output("wbs-headcounts-timecheck-container", "children"),
#         Output("wbs-institution-textarea-timecheck-container", "children"),
#         Output("wbs-computing-timecheck-container", "children"),
#         #
#         Output("wbs-headcounts-confirm-container-container", "hidden"),
#         #
#         Output("wbs-store-confirm-initial", "data"),
#         Output("wbs-store-confirm", "data"),
#     ],
#     [
#         Input("wbs-phds-authors", "value"),  # user/setup_institution_components()
#         Input("wbs-faculty", "value"),  # user/setup_institution_components()
#         Input("wbs-scientists-post-docs", "value"),  # user/setup_institution_components
#         Input("wbs-grad-students", "value"),  # user/setup_institution_components()
#         Input("wbs-cpus", "value"),  # user/setup_institution_components()
#         Input("wbs-gpus", "value"),  # user/setup_institution_components()
#         Input("wbs-textarea", "value"),  # user/setup_institution_components()
#         #
#         Input("wbs-headcounts-confirm-yes", "n_clicks"),  # user-only
#         Input("wbs-table-confirm-yes", "n_clicks"),  # user-only
#         Input("wbs-computing-confirm-yes", "n_clicks"),  # user-only
#     ],
#     [
#         State("url", "pathname"),
#         State("wbs-current-snapshot-ts", "value"),
#         #
#         State("wbs-data-table", "data"),
#         #
#         State("wbs-institution-values-first-time-flag", "data"),
#         #
#         State("wbs-store-confirm-initial", "data"),
#         State("wbs-store-confirm", "data"),
#     ],
#     prevent_initial_call=True,
# )
# def push_institution_values(  # pylint: disable=R0913
#     phds: types.DashVal,
#     faculty: types.DashVal,
#     sci: types.DashVal,
#     grad: types.DashVal,
#     #
#     cpus: types.DashVal,
#     gpus: types.DashVal,
#     text: str,
#     #
#     _: int,
#     __: int,
#     ___: int,
#     # state(s)
#     s_urlpath: str,
#     s_snap_ts: types.DashVal,
#     #
#     s_table: uut.WebTable,
#     #
#     s_first_time: bool,
#     #
#     s_hc_conf_ts: int,
#     s_table_conf_ts: int,
#     s_comp_conf_ts: int,
# ) -> Tuple[
#     bool,
#     #
#     List[html.Label],
#     List[html.Label],
#     List[html.Label],
#     #
#     bool,
#     #
#     int,
#     int,
#     int,
# ]:
#     """Push the institution's values."""
#     logging.warning(
#         f"'{du.triggered()}' -> push_institution_values() ({s_first_time=})"
#     )

#
