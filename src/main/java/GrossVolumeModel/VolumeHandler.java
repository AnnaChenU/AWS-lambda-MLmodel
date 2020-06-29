package GrossVolumeModel;

import java.lang.reflect.Method;
import java.net.MalformedURLException;
import java.net.URLClassLoader;
import java.net.URL;
import java.io.*;
import java.util.*;
import java.nio.charset.*;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.LambdaLogger;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.FieldNamingPolicy;
import hex.genmodel.GenModel;
import hex.genmodel.easy.EasyPredictModelWrapper;
import hex.genmodel.easy.RowData;
import hex.genmodel.easy.exception.PredictException;
import hex.genmodel.easy.prediction.RegressionModelPrediction;


public class VolumeHandler implements RequestHandler<RequestList, RequestList> {
    Gson gson = new GsonBuilder().setFieldNamingPolicy(FieldNamingPolicy.UPPER_CAMEL_CASE).create();
    private static final String modelClassName = "GrossVolumeModel_gbm";
    //private static final String targetName = "FinalVolume_predicted";

    @Override
    public RequestList handleRequest(RequestList event, Context context) {
        LambdaLogger logger = context.getLogger();
        logger.log("EVENT: " + gson.toJson(event));
        logger.log("EVENT TYPE: " + event.getClass().toString());

        List<RowData> inputs = event.getRequestItem();
        predictVolume(inputs, generateModel());  // update finalVolume_pred field
        logger.log("RESULT: " + gson.toJson(event));
        return event;
    }

    private EasyPredictModelWrapper generateModel() {
        GenModel rawModel = new GrossVolumeModel_gbm();
        EasyPredictModelWrapper model = new EasyPredictModelWrapper(new EasyPredictModelWrapper.Config()
                .setModel(rawModel).setConvertUnknownCategoricalLevelsToNa(true));
        return model;
    }

    private void predictVolume(List<RowData> inputs, EasyPredictModelWrapper model) {
        RowData row = new RowData();
        for (RowData input : inputs) {
            try {
                RegressionModelPrediction p = model.predictRegression(input);
                input.put("finalVolume_pred", "" + p.value);
            } catch (PredictException e) {
                e.printStackTrace();
            }
        }
    }

    public final static RowData pojo2RowData(Object obj) {
        RowData row = new RowData();
        try {
            Class<? extends Object> c = obj.getClass();
            Method m[] = c.getMethods();
            for (int i = 0; i < m.length; i++) {
                if (m[i].getName().indexOf("get") == 0) {
                    String name = m[i].getName().substring(3);
                    row.put(name, m[i].invoke(obj, new Object[0]));
                }
            }
        } catch (Throwable e) {
            e.printStackTrace();
        }
        return row;
    }
}


