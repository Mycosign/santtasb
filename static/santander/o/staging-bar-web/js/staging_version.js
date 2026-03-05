/*1651789682000*/
AUI.add("liferay-staging-version", function(A) {
    var StagingBar = Liferay.StagingBar;
    var MAP_CMD_REVISION = {
        redo: "redo_layout_revision",
        undo: "undo_layout_revision"
    };
    var MAP_TEXT_REVISION = {
        redo: "Are you sure you want to redo your last changes?",
        undo: "Are you sure you want to undo your last changes?"
    };
    A.mix(StagingBar, {
        _cleanup: function _cleanup() {
            var instance = this;
            if (instance._eventHandles) A.Array.invoke(instance._eventHandles, "detach")
        },
        _getNotification: function _getNotification() {
            var instance = this;
            var notification =
                instance._notification;
            if (!notification) {
                notification = new Liferay.Notice({
                    closeText: false,
                    content: "There was an unexpected error. Please refresh the current page.",
                    noticeClass: "hide",
                    timeout: 1E4,
                    toggleText: false,
                    type: "warning",
                    useAnimation: true
                });
                instance._notification = notification
            }
            return notification
        },
        _onInit: function _onInit() {
            var instance = this;
            instance._cleanup();
            var namespace = instance._namespace;
            var eventHandles = [Liferay.on(namespace + "redo", instance._onRevisionChange, instance, "redo"), Liferay.on(namespace +
                "submit", instance._onSubmit, instance), Liferay.on(namespace + "undo", instance._onRevisionChange, instance, "undo"), Liferay.on(namespace + "viewHistory", instance._onViewHistory, instance)];
            var layoutRevisionDetails = A.one("#" + namespace + "layoutRevisionDetails");
            var layoutRevisionStatus = A.one("#" + namespace + "layoutRevisionStatus");
            if (layoutRevisionDetails) eventHandles.push(Liferay.after("updatedLayout", function() {
                Liferay.Util.fetch(instance.markAsReadyForPublicationURL).then(function(response) {
                    return response.text()
                }).then(function(response) {
                    layoutRevisionDetails.plug(A.Plugin.ParseContent);
                    layoutRevisionDetails.setContent(response);
                    Liferay.fire("updatedStatus")
                })["catch"](function() {
                    layoutRevisionDetails.setContent("There was an unexpected error. Please refresh the current page.")
                })
            }));
            if (layoutRevisionStatus) Liferay.after("updatedStatus", function() {
                Liferay.Util.fetch(instance.layoutRevisionStatusURL).then(function(response) {
                    return response.text()
                }).then(function(response) {
                    layoutRevisionStatus.plug(A.Plugin.ParseContent);
                    layoutRevisionStatus.setContent(response)
                })["catch"](function() {
                    layoutRevisionStatus.setContent("There was an unexpected error. Please refresh the current page.")
                })
            });
            instance._eventHandles = eventHandles
        },
        _onRevisionChange: function _onRevisionChange(event, type) {
            var instance = this;
            var cmd = MAP_CMD_REVISION[type];
            var confirmText = MAP_TEXT_REVISION[type];
            if (confirm(confirmText)) instance._updateRevision(cmd, event.layoutRevisionId, event.layoutSetBranchId)
        },
        _onSubmit: function _onSubmit(event) {
            var instance = this;
            var namespace = instance._namespace;
            var layoutRevisionDetails = A.one("#" + namespace + "layoutRevisionDetails");
            var layoutRevisionInfo = layoutRevisionDetails.one(".layout-revision-info");
            if (layoutRevisionInfo) layoutRevisionInfo.addClass("loading");
            var submitLink = A.one("#" + namespace + "submitLink");
            if (submitLink) submitLink.html("Loading" + "...");
            Liferay.Util.fetch(event.publishURL).then(function() {
                if (event.incomplete) location.href = event.currentURL;
                else Liferay.fire("updatedLayout")
            })["catch"](function() {
                layoutRevisionDetails.addClass("alert alert-danger");
                layoutRevisionDetails.setContent("There was an unexpected error. Please refresh the current page.")
            })
        },
        _onViewHistory: function _onViewHistory() {
            Liferay.Util.openWindow({
                dialog: {
                    after: {
                        destroy: function destroy() {
                            window.location.reload()
                        }
                    },
                    destroyOnHide: true
                },
                title: "History",
                uri: StagingBar.viewHistoryURL
            })
        },
        _updateRevision: function _updateRevision(cmd, layoutRevisionId, layoutSetBranchId) {
            var instance = this;
            var updateLayoutData = {
                cmd: cmd,
                doAsUserId: themeDisplay.getDoAsUserIdEncoded(),
                layoutRevisionId: layoutRevisionId,
                layoutSetBranchId: layoutSetBranchId,
                p_auth: Liferay.authToken,
                p_l_id: themeDisplay.getPlid(),
                p_v_l_s_g_id: themeDisplay.getSiteGroupId()
            };
            Liferay.Util.fetch(themeDisplay.getPathMain() + "/portal/update_layout", {
                body: Liferay.Util.objectToFormData(updateLayoutData),
                method: "POST"
            }).then(function() {
                window.location.reload()
            })["catch"](function() {
                instance._getNotification().show()
            })
        },
        destructor: function destructor() {
            var instance = this;
            instance._cleanup()
        }
    });
    Liferay.on("initStagingBar", StagingBar._onInit, StagingBar)
}, "", {
    requires: ["aui-button", "liferay-staging"]
});