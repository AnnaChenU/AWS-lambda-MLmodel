package GrossVolumeModel;
import java.util.List;
import com.google.gson.annotations.Expose;
import com.google.gson.annotations.SerializedName;
import hex.genmodel.easy.RowData;

public class RequestList {
    @SerializedName("requestItem")
    @Expose
    private List<RowData> requestItem = null;

    /**
     * No args constructor for use in serialization
     *
     */
    public RequestList() {
    }

    /**
     *
     * @param requestItem
     */
    public RequestList(List<RowData> requestItem) {
        super();
        this.requestItem = requestItem;
    }

    public List<RowData> getRequestItem() {
        return requestItem;
    }

    public void setRequestItem(List<RowData> requestItem) {
        this.requestItem = requestItem;
    }
}