package com.example.snipee;
import android.graphics.Point;

public class Coord_Interpolator {
    private float[] lastPoint;

    public Coord_Interpolator(){
        this.lastPoint = new float[]{(float)-1, (float)-1};
    }

    public float[] interpolate(float xin, float yin){
        float[] result = new float[2];
        if (lastPoint[0] == -1 && lastPoint[1] == -1){
            //first point will not be interpolated
            lastPoint[0] = xin;
            lastPoint[1] = yin;
            result[0] = xin;
            result[1] = yin;
        }
        else{
            //common case
            result[0] = xin + (xin-lastPoint[0])/2;
            result[1] = yin + (yin-lastPoint[1])/2;

            lastPoint[0] = result[0];
            lastPoint[1] = result[1];
        }
        return result;

    }
}
