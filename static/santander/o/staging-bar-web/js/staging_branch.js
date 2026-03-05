/*1651789682000*/
AUI.add("liferay-staging-branch", function(A) {
    var Lang = A.Lang;
    var StagingBar = Liferay.StagingBar;
    A.mix(StagingBar, {
        _getBranchDialog: function _getBranchDialog() {
            var instance = this;
            var branchDialog = instance._branchDialog;
            if (!branchDialog) {
                var namespace = instance._namespace;
                branchDialog = Liferay.Util.Window.getWindow({
                    dialog: {
                        bodyContent: A.one("#" + namespace + "addBranch").show()
                    },
                    title: "Branch"
                });
                instance._branchDialog = branchDialog
            }
            return branchDialog
        },
        addBranch: function addBranch(dialogTitle) {
            var instance =
                this;
            var branchDialog = instance._getBranchDialog();
            if (Lang.isValue(dialogTitle)) branchDialog.set("title", dialogTitle);
            branchDialog.show()
        }
    })
}, "", {
    requires: ["liferay-staging"]
});