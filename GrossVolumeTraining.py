try:
    import os
    import os.path
    from os import path
    import h2o
    from h2o.estimators.gbm import H2OGradientBoostingEstimator
    import random
    import sys
    import json
    import boto3
    from botocore.exceptions import ClientError
    from botocore.exceptions import NoCredentialsError
   

except Exception as e:
    print("some modules missing {}".format(e))

INPUT_PATH = os.getenv('VH_INPUTS_DIR', '.inputs/')
OUTPUT_PATH = os.getenv('VH_OUTPUTS_DIR', '.outputs/')


class GrossVolumeTraining(object):
    def __init__(self):
        h2o.init(max_mem_size='1G')

        h2o.remove_all()

        # self.file_path = file_path

        self.split_seed = random.randrange(sys.maxsize)

        self.col_headers = ['C1', 'FinalWeight', 'FinalVolume', 'BookedWeight', 'BookedVolume', 'DepartureDayOfYear',
                            'ArrivalDayOfYear', 'DepartureWeek', 'ArrivalWeek', 'DepartureWeekDay', 'ArrivalWeekDay',
                            'Origin', 'Destination', 'FlightNumber', 'Suffix', 'Equipment', 'EquipmentInHouse',
                            'TransportMode', 'Distance', 'CaptureWeightCapacity', 'CaptureVolumeCapacity', 'LegNumber',
                            'Piecese', 'ChargeableWeight', 'Ndo', 'StatusCode', 'PartShipmentIndicator', 'NetCharge',
                            'AllotmentCode', 'SpaceAllocationCode', 'Agent', 'POS', 'ProductCode', 'Density', 'Days']

        self.col_types = ['numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'numeric',
                          'numeric', 'numeric', 'numeric', 'enum', 'enum', 'enum', 'enum', 'enum', 'enum', 'enum',
                          'numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'numeric', 'enum',
                          'numeric', 'numeric', 'enum', 'enum', 'enum', 'enum', 'enum', 'numeric', 'numeric']

        self.gbm_params = {'model_id': 'GrossVolumeModel_gbm',
                           'nfolds': 0,
                           'keep_cross_validation_models': False,
                           'keep_cross_validation_predictions': True,
                           'keep_cross_validation_fold_assignment': False,
                           'score_each_iteration': False,
                           'score_tree_interval': 5,
                           'fold_assignment': 'AUTO',
                           'fold_column': None,
                           'response_column': 'FinalVolume',
                           'ignored_columns': ['C1',
                                               'TransportMode',
                                               'ProductCode',
                                               'SpaceAllocationCode'],
                           'ignore_const_cols': True,
                           'offset_column': None,
                           'weights_column': None,
                           'balance_classes': False,
                           'class_sampling_factors': None,
                           'max_after_balance_size': 5.0,
                           'max_confusion_matrix_size': 20,
                           'max_hit_ratio_k': 0,
                           'min_rows': 1.0,
                           'nbins': 20,
                           'nbins_top_level': 1024,
                           'nbins_cats': 1024,
                           'r2_stopping': 1.7976931348623157e+308,
                           'stopping_rounds': 3,
                           'stopping_metric': 'RMSE',
                           'stopping_tolerance': 0.0010019164953871014,
                           'max_runtime_secs': 658812317797974.0,
                           'seed': 6785859302972478466,
                           'build_tree_one_node': False,
                           'learn_rate': 0.05,
                           'learn_rate_annealing': 1.0,
                           'distribution': 'gaussian',
                           'quantile_alpha': 0.5,
                           'tweedie_power': 1.5,
                           'huber_alpha': 0.9,
                           'checkpoint': None,
                           'sample_rate': 0.7,
                           'sample_rate_per_class': None,
                           'col_sample_rate_change_per_level': 1.0,
                           'col_sample_rate_per_tree': 0.7,
                           'min_split_improvement': 1e-05,
                           'histogram_type': 'AUTO',
                           'max_abs_leafnode_pred': 1.7976931348623157e+308,
                           'pred_noise_bandwidth': 0.0,
                           'categorical_encoding': 'AUTO',
                           'calibrate_model': False,
                           'calibration_frame': None,
                           'custom_metric_func': None,
                           'custom_distribution_func': None,
                           'export_checkpoints_dir': None,
                           'monotone_constraints': None,
                           'check_constant_response': True,
                           'max_depth': 6,
                           'ntrees': 1235}

    def get_data(self, src_bucket="cargo.ml.training", obj_name="training_sample.csv"):
        # boto3.setup_default_session(region_name='us-west-2')
        # s3_client = boto3.client('s3', aws_access_key_id=ACCESS_KID, aws_secret_access_key=ACCESS_KEY)
        input_path = os.path.join(INPUT_PATH, 'training_sample_input/training_sample.csv')
        # s3_client.download_file(src_bucket, obj_name, input_path)

        df_raw = h2o.import_file(input_path, parse=False)
        setup = h2o.parse_setup(df_raw,
                                destination_frame="training.hex",
                                header=1,
                                column_names=self.col_headers,
                                column_types=self.col_types)
        df = h2o.parse_raw(h2o.parse_setup(df_raw),
                           id='training.csv',
                           first_line_is_header=1)

        print("Input dataframe: ", df)
        return df

    def split_dataframe(self, df, ratios=[.9], seed=None):
        train, test = df.split_frame(ratios=ratios, seed=seed)
        return train, test

    def train_gbm(self):
        dt_all = self.get_data()

        dt_train, dt_test = self.split_dataframe(dt_all, seed=self.split_seed)

        y = 'FinalVolume'  # response column

        final_gbm = H2OGradientBoostingEstimator(**self.gbm_params)

        print("# Start training......")
        final_gbm.train(y=y, training_frame=dt_train, validation_frame=dt_test)

        print('# Downloading model as pojo file......')

        try:
            print("Dowloaing pojo.")
            final_gbm.download_pojo(os.path.join(OUTPUT_PATH, 'gbm_model.java'))
            if path.exists(os.path.join(OUTPUT_PATH, 'gbm_model.java')):
                print("Pojo downloaded successfully")
            else:
                print("No pojo!!!!!!!!!")

        except Exception as ex:
            print("POJO downloading error: {}".format(ex))

        print(final_gbm)

        print("# Training done.")

        # self.upload_model()


def main():
    print("Start!")


if __name__ == "__main__":
    obj = GrossVolumeTraining()
    obj.train_gbm()
    h2o.shutdown()
