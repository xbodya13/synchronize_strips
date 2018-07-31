bl_info = {
    "name": "Synchronize selected strips with active",
    "category": "Sequencer",
    "version": (1, 0),
    "blender": (2, 7, 9),
    "location": "",
    "description": "",
    "wiki_url": "",
    "tracker_url": ""
}

import bpy
import subprocess
import datetime
import pickle
import os



class SynchronizeStrips(bpy.types.Operator):
    """Split strip by scenes"""
    bl_idname = "synchronize.synchronize_strips"
    bl_label = "-Synchronize strips"
    bl_options = {'REGISTER', 'UNDO'}

    sampling_rate=bpy.props.FloatProperty(name="Sampling rate",description="Higher values increase probability of good result but also increase processing time", min=1, default=10000,max=44000)


    def get_strip_settings(self,strip):
        if strip.type=='SOUND':
            return ((strip,strip.frame_final_start),
            (os.path.normpath(bpy.path.abspath(strip.sound.filepath)),
             (strip.animation_offset_start+strip.frame_offset_start)/self.fps,
             strip.frame_final_duration/self.fps))

        if strip.type=='META':
            sound_strips=[sequence for sequence in strip.sequences if sequence.type=='SOUND']
            if len(sound_strips)==1:
                sound_strip=sound_strips[0]

                overlap=strip.frame_final_start-sound_strip.frame_final_start
                if overlap<0:
                    overlap=0
                clip_start=(sound_strip.animation_offset_start + sound_strip.frame_offset_start+overlap)/self.fps
                clip_length=(min(strip.frame_final_end,sound_strip.frame_final_end)-max(strip.frame_final_start,sound_strip.frame_final_start))/self.fps

                return ((strip,max(strip.frame_final_start, sound_strip.frame_final_start)),
                (os.path.normpath(bpy.path.abspath(sound_strip.sound.filepath)),
                clip_start,
                clip_length))
        return None


    def check(self, context):
        return True

    # def draw(self, context):
    #     pass



    @classmethod
    def poll(self, context):
        if context.scene.sequence_editor!=None:
            return True
        else:
            return False




    def before_stop(self,context):
        context.window_manager.event_timer_remove(self.timer)
        context.window_manager.progress_end()
        context.area.header_text_set()




    def modal(self, context, event):
        # print("MODAL")


        if event.type=='ESC':
            # print("CANCEL")
            try:self.p.terminate()
            except:pass
            self.before_stop(context)
            return {'CANCELLED'}


        if event.type=='TIMER':
            # print("TIMER")
            self.count += 1
            context.window_manager.progress_update(100*(self.count%2))
            context.area.header_text_set("Press ESC to cancel. Time elapsed: " + str(datetime.datetime.now() - self.start_time).split(".")[0])

            # out_text = self.p.communicate(timeout=0.5)
            # return_code = self.p.returncode
            out_text=None
            return_code=None
            try:
                out_text=self.p.communicate(timeout=0.5)
                return_code=self.p.returncode
                # print(out_text)
            except subprocess.TimeoutExpired :pass
            # except:
            #     self.report({'ERROR'}, "Error")
            #     self.before_stop(context)
            #     return {'CANCELLED'}
            print(out_text)
            if return_code!=None:
                print(pickle.loads(out_text[0]))
                if return_code==0:


                    print("SYNC")

                    # shifts=[0 for strip in self.selected_strips]
                    shifts=pickle.loads(out_text[0])
                    active_strip,active_start_point=self.active_strip

                    for (selected_strip, selected_start_point),shift in zip(self.selected_strips,shifts):
                            selected_strip.frame_start += active_start_point - selected_start_point + round(shift*self.fps)

                    self.report({'INFO'}, "Synchronized.Time elapsed: {} ".format(str(datetime.datetime.now() - self.start_time).split(".")[0]))
                    self.before_stop(context)
                    return {'FINISHED'}
                else:
                    self.report({'ERROR'}, "Error")
                    self.before_stop(context)
                    return {'CANCELLED'}

        return {'RUNNING_MODAL'}


    def invoke(self, context, event):
        # print("INVOKE")
        return context.window_manager.invoke_props_dialog(self)


    def execute(self, context):
        # print("EXECUTE")

        self.fps = context.scene.render.fps / context.scene.render.fps_base
        active_strip=context.scene.sequence_editor.active_strip
        temp_settings=self.get_strip_settings(active_strip)
        if temp_settings!=None:
            self.active_strip,active_send_data=temp_settings
            self.selected_strips=[]
            selected_send_data=[]
            for selected_strip in context.selected_editable_sequences:
                temp_settings=self.get_strip_settings(selected_strip)
                if temp_settings!=None:
                    (temp_strip,temp_start_point),temp_send_data=temp_settings
                    if temp_strip!=active_strip:
                        self.selected_strips.append((temp_strip,temp_start_point))
                        selected_send_data.append(temp_send_data)
            if len(selected_send_data)>=1:


                send_data=(active_send_data,selected_send_data,self.sampling_rate)

                sync_core="E:/LW/MP/free/gm/blender-2.79b-windows64/2.79/scripts/addons/sync_core.py"
                command = "python {}".format(sync_core)
                # self.p = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # pickle.dump((1, 2, 3), self.p.stdin)


                try:
                    self.p = subprocess.Popen(command, stdin=subprocess.PIPE,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # self.p.communicate(b"AAA",timeout=0.5)
                    pickle.dump(send_data, self.p.stdin)

                except subprocess.TimeoutExpired:pass
                # except:
                #     self.report({'ERROR'}, "Error")
                #     return {'CANCELLED'}


                self.count = 0
                self.start_time=datetime.datetime.now()
                self.timer = context.window_manager.event_timer_add(0.5, context.window)


                context.window_manager.modal_handler_add(self)
                context.window_manager.progress_begin(0, 100)
                context.area.header_text_set("Press ESC to cancel. Time elapsed: " + str(datetime.datetime.now() - self.start_time).split(".")[0])

                return {'RUNNING_MODAL'}
            else:
                return {'CANCELLED'}






def register():
    # os.system('cls')
    # print("I AM REGISTER")
    bpy.utils.register_module(__name__)
    # print("REGISTER FINISHED")


def unregister():
    # print("I AM UNREGISTER")
    bpy.utils.unregister_module(__name__)
    # print("UNREGISTER FINISHED")


